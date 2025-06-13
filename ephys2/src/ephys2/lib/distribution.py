'''
Worker distribution utilities for MPI parallel processing
'''
import math
from typing import Tuple, Optional, List, Dict, Any, Union
import numpy as np
import json

from ephys2.lib.singletons import logger

class WorkerDistribution:
    """
    Utility class to handle validation and calculation of worker data distribution
    for parallel processing. Ensures all workers get data and provides recommended
    parameters when the distribution would be invalid.
    """
    
    @staticmethod
    def calculate_chunks(total_size: Union[int, Dict[str, int]], batch_size: int, batch_overlap: int) -> int:
        """
        Calculate the number of chunks given the total data size and batch parameters.
        
        Args:
            total_size: Total size of the dataset (either an integer or dictionary of channel group sizes)
            batch_size: Size of each batch
            batch_overlap: Overlap between batches
            
        Returns:
            Number of chunks the data will be split into
        """
        if batch_size <= batch_overlap:
            raise ValueError(f"Batch overlap ({batch_overlap}) must be less than batch size ({batch_size})")
        
        # If total_size is a dictionary (MultiBatch case with channel groups), use the maximum size
        if isinstance(total_size, dict):
            if not total_size:  # Empty dictionary
                return 0
            effective_size = max(total_size.values())
        else:
            effective_size = total_size
            
        effective_chunk_size = batch_size - batch_overlap
        return math.ceil((effective_size - batch_overlap) / effective_chunk_size) if effective_size > 0 else 0

    @staticmethod
    def validate_distribution(total_size: Union[int, Dict[str, int]], batch_size: int, batch_overlap: int, n_workers: int) -> bool:
        """
        Validate that the distribution parameters will allow all workers to get data.
        
        Args:
            total_size: Total size of the dataset (either an integer or dictionary of channel group sizes)
            batch_size: Size of each batch
            batch_overlap: Overlap between batches
            n_workers: Number of workers
            
        Returns:
            True if all workers will get data, False otherwise
        """
        total_chunks = WorkerDistribution.calculate_chunks(total_size, batch_size, batch_overlap)
        return total_chunks >= n_workers
        
    @staticmethod
    def get_workers_without_data(total_size: Union[int, Dict[str, int]], batch_size: int, batch_overlap: int, n_workers: int) -> List[int]:
        """
        Calculate which workers will not receive data.
        
        Args:
            total_size: Total size of the dataset (either an integer or dictionary of channel group sizes)
            batch_size: Size of each batch
            batch_overlap: Overlap between batches
            n_workers: Number of workers
            
        Returns:
            List of worker ranks that won't receive data
        """
        total_chunks = WorkerDistribution.calculate_chunks(total_size, batch_size, batch_overlap)
        return list(range(total_chunks, n_workers)) if total_chunks < n_workers else []

    @staticmethod
    def calculate_recommended_parameters(total_size: Union[int, Dict[str, int]], batch_size: int, batch_overlap: int, 
                                         n_workers: int) -> Tuple[int, int]:
        """
        Calculate recommended batch size and overlap when the current parameters
        would result in some workers not getting data.
        
        Args:
            total_size: Total size of the dataset (either an integer or dictionary of channel group sizes)
            batch_size: Current batch size
            batch_overlap: Current batch overlap
            n_workers: Number of workers
            
        Returns:
            Tuple of (recommended_batch_size, recommended_batch_overlap)
        """
        # If total_size is a dictionary (MultiBatch case with channel groups), use the maximum size
        if isinstance(total_size, dict):
            if not total_size:  # Empty dictionary
                return batch_size, batch_overlap  # Cannot recommend parameters for empty data
            effective_size = max(total_size.values())
        else:
            effective_size = total_size
            
        # Calculate the current overlap ratio
        overlap_ratio = batch_overlap / batch_size if batch_size > 0 else 0
        
        # Calculate minimum effective chunk size needed per worker
        min_effective_chunk = math.ceil(effective_size / n_workers)
        
        # Calculate batch size from effective chunk size and overlap ratio
        if overlap_ratio < 1:
            max_batch_size = math.ceil((math.ceil(min_effective_chunk / (1 - overlap_ratio)) + 1) / 2) * 2
        else:
            # If overlap ratio is 1 or greater, just add 1 to the effective chunk
            max_batch_size = min_effective_chunk + 1
        
        # Calculate corresponding new overlap
        new_overlap = math.floor(max_batch_size * overlap_ratio)
        
        # Make sure the effective chunk size is at least the minimum required
        if max_batch_size - new_overlap < min_effective_chunk:
            max_batch_size = min_effective_chunk + new_overlap
        
        return max_batch_size, new_overlap

    @staticmethod
    def validate_file_metadata(file_obj: Any, batch_size: int, batch_overlap: int, n_workers: int,
                              rank: int = 0) -> Optional[str]:
        """
        Validate distribution based on metadata in a file.
        
        Args:
            file_obj: File object containing metadata (must have attrs dictionary with total_size)
            batch_size: Size of each batch
            batch_overlap: Overlap between batches
            n_workers: Number of workers
            rank: Current worker rank
            
        Returns:
            Error message if validation fails, None if it passes or can't be validated
        """
        if hasattr(file_obj, 'attrs') and 'total_size' in file_obj.attrs:
            # First try to use channel_group_sizes if available
            if 'channel_group_sizes' in file_obj.attrs:
                try:
                    # Parse the JSON string to get the dictionary
                    channel_group_sizes = json.loads(file_obj.attrs['channel_group_sizes'])
                    
                    if rank == 0:
                        max_size = max(channel_group_sizes.values()) if channel_group_sizes else 0
                        logger.debug(f"Data distribution check using channel groups: max_size={max_size}, "
                                f"total_size={file_obj.attrs['total_size']}, batch_size={batch_size}, "
                                f"batch_overlap={batch_overlap}, workers={n_workers}")
                    
                    # Use the channel group sizes for validation
                    if not WorkerDistribution.validate_distribution(channel_group_sizes, batch_size, batch_overlap, n_workers):
                        workers_without_data = WorkerDistribution.get_workers_without_data(
                            channel_group_sizes, batch_size, batch_overlap, n_workers)
                        
                        # Format the error message
                        return WorkerDistribution.format_error_message(
                            channel_group_sizes, batch_size, batch_overlap, n_workers, workers_without_data)
                    
                    return None  # Validation passed
                except Exception as e:
                    # Fall back to using total_size if there's an error parsing channel_group_sizes
                    if rank == 0:
                        logger.warn(f"Error parsing channel_group_sizes, falling back to total_size: {str(e)}")
            
            # Fall back to using total_size
            total_size = file_obj.attrs['total_size']
            
            if rank == 0:
                # For dictionary total_size, log the maximum value
                if isinstance(total_size, dict):
                    max_size = max(total_size.values()) if total_size else 0
                    logger.debug(f"Data distribution check: max_total_size={max_size}, batch_size={batch_size}, "
                            f"batch_overlap={batch_overlap}, workers={n_workers}")
                else:
                    logger.debug(f"Data distribution check: total_size={total_size}, batch_size={batch_size}, "
                            f"batch_overlap={batch_overlap}, workers={n_workers}")
                
            # Use the WorkerDistribution utility to validate
            if not WorkerDistribution.validate_distribution(total_size, batch_size, batch_overlap, n_workers):
                workers_without_data = WorkerDistribution.get_workers_without_data(
                    total_size, batch_size, batch_overlap, n_workers)
                
                # Format the error message
                return WorkerDistribution.format_error_message(
                    total_size, batch_size, batch_overlap, n_workers, workers_without_data)
        
        return None  # No validation possible or validation passed

    @staticmethod
    def validate_empirical(worker_has_data: List[bool], total_size_estimate: Union[int, Dict[str, int]], 
                          batch_size: int, batch_overlap: int, n_workers: int) -> Optional[str]:
        """
        Validate distribution based on empirical results (which workers actually got data).
        
        Args:
            worker_has_data: List of booleans indicating which workers got data
            total_size_estimate: Estimated total data size (integer or dictionary of channel group sizes)
            batch_size: Size of each batch
            batch_overlap: Overlap between batches
            n_workers: Number of workers
            
        Returns:
            Error message if validation fails, None if it passes
        """
        workers_without_data = [i for i, has_data in enumerate(worker_has_data) if not has_data]
        
        if workers_without_data:
            return WorkerDistribution.format_error_message(
                total_size_estimate, batch_size, batch_overlap, n_workers, workers_without_data)
                
        return None  # All workers got data

    @staticmethod
    def format_error_message(total_size: Union[int, Dict[str, int]], batch_size: int, batch_overlap: int, 
                             n_workers: int, workers_without_data: list) -> str:
        """
        Format an error message with recommended parameters when workers won't get data.
        
        Args:
            total_size: Total size of the dataset (integer or dictionary of channel group sizes)
            batch_size: Current batch size
            batch_overlap: Current batch overlap
            n_workers: Number of workers
            workers_without_data: List of worker ranks that won't get data
            
        Returns:
            Formatted error message with recommendations
        """
        # Calculate recommended parameters
        max_batch_size, new_overlap = WorkerDistribution.calculate_recommended_parameters(
            total_size, batch_size, batch_overlap, n_workers)
        
        # Calculate maximum number of workers that could be used
        total_chunks = WorkerDistribution.calculate_chunks(total_size, batch_size, batch_overlap)
        
        # For dictionary total_size, include information about the maximum size
        if isinstance(total_size, dict):
            max_size = max(total_size.values()) if total_size else 0
            size_info = f"Maximum channel group size: {max_size} (from {len(total_size)} channel groups)"
        else:
            size_info = f"Data size: {total_size}"
        
        return (
            f"Error: Workers {workers_without_data} will not receive any data with the current distribution parameters.\n"
            f"{size_info}, batch_size={batch_size}, batch_overlap={batch_overlap}\n"
            f"Maximum batch_size: {max_batch_size} with batch_overlap: {new_overlap}\n"
            f"Or use fewer workers (maximum: {max(1, total_chunks)})."
        ) 