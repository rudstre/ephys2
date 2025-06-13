function  spkB = NTM(spikes,varargin)
%Perform normalized template matching on voltage data to detect spikes. The
%link to the manuscript describing the method is:

%https://www.biorxiv.org/content/early/2018/10/17/445585

%Input variables:
%spikes is a structure that contains the detected spikes via the initial round 
%of spikes sorting that is needed to calculate the templates that will be used for
%spike detection in NTM. The spikes structure contains the following
%fields:
% spikes.waveforms %Is a NxMxC matrix where N is the number of waveforms, M
%                  is the number of samples per waveform (window size in
%                  samples) and C is the number of electrode channels (e.g.
%                  4 in a tetrode). This set of waveforms should include
%                  all voltage threshold crossing events, including noise
%                  and multiunit activity, because this data is used to
%                  calculate Si, the similarity index threshold.
%                                                                   
% spikes.clusID %Is an Nx1 vector with the cluster ID of each spike
%                waveform. Values should be integers 
% 
% spikes.labels %Is an Nx1 logical vector that classifies each spike as
%                belonging to a single-unit (true) or multiunit/noise
%                (false). Templates will be calculated from single-unit
%                spikes.
%
% spikes.Fs      %Sampling rate of the voltage data (i.e. samples per
%                second)
%
% spikes.shadow  %Shadow period in milliseconds, period of time spike
%                detection is turned off after a spike is detected
%
%Optional input:
%Channel IDs   %1xC vector of integers denoting the channels where the
%              spikes in spikes.waveforms were detected. C is the number of channels 
%
%Other required data:
% The only other required variable is a TxSxL voltage data matrix (or set of matrices)
% individually stored as separate mat files. This is the data where spikes
% were detected in the initial round of spike sorting. T is the number of trials (can be 1 for a continuous recording)
% S is the number of samples (i.e. time domain) and L is the number of electrodes
% (or channels) used in the extracellular recording. 
%
%This function uses uipickfiles.m to access the mat files with the voltage
%   data. You can download the function at:
%   https://www.mathworks.com/matlabcentral/fileexchange/10867-uipickfiles-uigetfile-on-steroids
%
%Output variable:
%   spkB is a structure that contains the waveforms of detected spikes, spike times (in seconds) 
%   and trials in which the spike was detected. spkB contains M fields where M is
%   the number of files chosen by the user to be analyzed. The name of the field will be the name of
%   the chosen file. Each field is a nested structure with the following fields:
%
%   spkB.filename.waveforms is a Nx(M + jit)xC matrix containing all of the
%   spikes detected by NTM. N is number of waveforms, M = size(spikes.waveforms,2)
%   and C is the number of channels. jit is a variable defined in line 217 and its
%   default value is .5 ms. This jitter is used to add extra samples in the
%   newly detected spike waveforms for spike alignment. You can set jit to
%   zero but spike alignment will likely be harder afterwards (IMPORTANT:
%   spike alignment is not performed by NTM)
%
%   spkB.filename.trials is a Nx1 vector with the trial number (the row of the voltage data matrix in
%   the corresponding mat file) in which each spike was detected. 
%
%   spkB.filename.spiketimes is a Nx1 vector with the time (in seconds) in which
%   each spike happened at each trial. 
%
%   spkB.filename.unwrapped_times is spiketimes but computed continuously across
%   trials instead of within trials:
%
%   All of this means that the spike with shape spkB.filename.waveform(n,:,:) 
%   ocurred at time spkB.filename.spiketimes(n) in trial spkB.filename.trials(n)
%   in the voltage trace stored in the file called 'filename'. 
%
%
% First warning! This function DOES NOT preprocess the voltage data so if
% the data was common average referenced (recommended) and bandpass
% filtered (recommended) for the first round of sorting then the mat file 
% with the voltage data to be used in NTM must be filtered and common average referenced. 
%
% Second warning! NTM is a spike detection algorithm not clustering. You
% must align spike waveforms by their peaks and cluster the spike waveforms 
% in spkB.('filename').waveforms following spike detection with NTM.  
%
% Third warning! This is open source software and to best of our knowledge
% this code has been fully debugged but we are not responsible
% for any data-storage or -analysis issues that arise from using NTM.m. That 
% being said, please report any bugs or issues to:
%
% Keven J. Laboy-Juárez   klaboy@berkeley.edu
%
%   
%% Check that the format of input variables is correct
spFields = fieldnames(spikes); 
xx = {'waveforms','clusID','labels','Fs','shadow'};
crcFlag = cellfun(@(x) any(strcmpi(spFields,x)),xx); 
if(~all(crcFlag)) %One of the fields in the spikes structure was not provided
    xx = cellfun(@(x) [x,', '],xx,'un',0); 
    error(['Fields ',[xx{~crcFlag}],'are missing from the spikes structure'])
end    
%User did not provide channels to index from volatge data
if(nargin==1) 
    numCh = size(spikes.waveforms,3); 
    chns = 1:numCh; 
    disp(['Warning! Channel indices were not provided, channels that will be indexed from voltage data are: ',...
        num2str(chns)])
else
    chns = varargin{1};
    if(length(chns)~=size(spikes.waveforms,3)) %Number of channels provided does not match the number in spike waveforms
        error('Number of channels provided does not match the number in spike waveforms')
    end
end
if(nargin>2)
    error('Too many input arguments')
end
%Check if each spike has a cluster ID
if(size(spikes.waveforms,1)~=length(spikes.clusID))
    error('Each spike needs to have a cluster ID')
end
%Check that each clusID has a label
if(length(spikes.clusID)~=length(spikes.labels)) %There's a mismatch between # of clusters and # of labels
    error('Each spike needs to have a cluster ID and a label')
end
%Check shadow to see if it's too small
if(spikes.shadow<.6)
    button2 = questdlg(['The current shadow period is ',num2str(spikes.shadow),'ms which is smaller than the recommended .66ms.',...
        'Do you wish to proceed with the chosen value or would you like to change to .66ms'],'','Proceed','Change','Change');
    if(isequal(button2,'Change'))
        spikes.shadow = .66; 
    end
end
%Check if user has the uipickfiles function   
%% Allows user to choose files with voltage time series data to analyze. User can choose individual mat files or folders containing multiple mat files
try
    fname = uipickfiles(); %Allow user to choose files to load (they can be either mat files or folders with the mat files that the user wants to analyze)
catch
    error('uipickfiles.m not found in your matlab directory. You can download the function at: https://www.mathworks.com/matlabcentral/fileexchange/10867-uipickfiles-uigetfile-on-steroids')
end
fname = fname'; %Change to column array 
if(~iscell(fname))
    fname = {fname}; %Avoid compatibility issues by changing to a cell array
end
whdir = cellfun(@isdir,fname); %Check if the user chose directories
if(any(whdir)) %The user chose directories
   disp(['Warning! A folder/directory was chosen by the user. All mat files in each folder will be sequentially analyzed. Make sure that the order of mat files is correct',...
        ' or choose individual mat files in the correct order instead'])
   sz = find(whdir); %Identify directories 
   fls2add = cell(length(sz),1); %Store the names of the files that will be loaded  
    for i = 1:length(sz) %loop over directories to save file names
        posN = what(fname{sz(i)}); 
        if(isempty(posN.mat)) %Chosen folder has no mat files
            error(['Folder ',fname{sz(i)},' has no mat files. Voltage data must be stored in a mat file'])
        end
        fls2add{i} = cellfun(@(x) [fname{sz(i)},'\',x],posN.mat,'un',0); %Store file names to add. NOTE PATH FORMAT IS COMPATIBLE WITH WINDOWS NOT APPLE OS, change string format accordingly  
    end
    %Get the file names into fname
    fname = cellfun(@cellstr,fname,'un',0); %Change all the names into a cell array. This allows for proper concatenation in the following steps
    fname(sz) = fls2add; %Change filenames that are directories to the name of the mat files to be used
    fname = vertcat(fname{:});     
end
%% Initialize output structure 
tmpS = cell(length(fname)*2,1); [tmpS{1:2:end}] = deal(fname{:}); 
mpV = 1:2:length(tmpS);
for e = 1:length(fname) %Loop over file names to modify for using as fieldnames in spkB
    if(any(tmpS{mpV(e)}=='\')) %contains directory subdivisions, invalid for fieldnames
       tmpS{mpV(e)} = tmpS{mpV(e)}(((find(tmpS{mpV(e)}=='\',1,'last'))+1):end);
    end
    if(any(tmpS{mpV(e)}=='.')) %contains dots, invalid for fieldnames
        if(sum(tmpS{mpV(e)}=='.')==1) %Likely a file format descriptor (eliminate completely)
            tmpS{mpV(e)} = tmpS{mpV(e)}(1:(find(tmpS{mpV(e)}=='.')-1));
        else %More than one dot (This should not happen, filenames should not have dots in them!)
            tmpS{mpV(e)}(tmpS{mpV(e)}=='.')='_'; %Switch dots for underscore
        end
    end
    %Add extra quotation marks for use with eval
    tmpS{mpV(e)} = ['''',tmpS{mpV(e)},'''']; 
end
[tmpS{2:2:end}] = deal(',[],'); tmpS{end} = tmpS{end}(1:(end-1)); %Remove last coma
mstStr = [tmpS{:}];
spkB = eval(['struct(',mstStr,')']); %Output structure (one field for each file)
%% Extract templates and calculate detection thresholds for each unit
%extract templates and important information from the spikes stucture
un2use = unique(spikes.clusID(spikes.labels)); 
numU = length(un2use); %Number of units to be analyzed 
templates = zeros(numU,size(spikes.waveforms,2),size(spikes.waveforms,3)); %store templates
projs = zeros(size(spikes.waveforms,1),numU); %Allocate 
normA = @(x) bsxfun(@times,x,1./sqrt(sum(x.^2,2))); %Scaling factor for NTM (divide by l2-norm)
ClassT = zeros(1,numU); %Allocate memory for spike detection thresholds 
for e = 1:length(un2use) %Loop over units to calculate preliminary templates and optimal theshold
    templates(e,:,:) = mean(spikes.waveforms(spikes.clusID==un2use(e),:,:),1);
    projs(:,e) =  sum(bsxfun(@times,normA(reshape(spikes.waveforms,size(spikes.waveforms,1),size(spikes.waveforms,2)*length(chns))),normA(reshape(templates(e,:,:),1,[]))),2); 
    mp =  min(projs(:,e)); mxp = max(projs(:,e));
    edges = mp:(abs(mxp-mp)/200):mxp; %edges for binning similarity indices
    %Calculate thresholds
    xtrue =  projs(spikes.clusID==un2use(e),e); xtrue = histc(xtrue,edges); xtrue = xtrue./sum(xtrue); %Projection values for waveforms in the class
    xother = projs(spikes.clusID~=un2use(e),e); xother = histc(xother,edges); xother = xother./sum(xother);  %Projection values for waveforms of other classes
    %calculate ROC curves for optimal threshold calculation
    fA = arrayfun(@(x) sum(xother(x:end)),1:length(edges)); %False alarm rate for each threshold
    tP = arrayfun(@(x) sum(xtrue(x:end)),1:length(edges)); %percent correct for each threshold
    tindx = max(find(tP-fA==max(tP-fA)));
    ClassT(e) = edges(tindx); %Optimal threshold that maximizes percent correct
    %%plot classification statistics
    figure()
    plot(edges,xtrue,'-r','LineWidth',3)
    hold on
    plot(edges,xother,'-b','LineWidth',3)
    title(['Classification performance for cluster ',num2str(un2use(e)),': FA=',num2str(fA(tindx)),' TP=',num2str(tP(tindx))])
    %FA is false alarm rate, TP is true positive rate
    legend(['Cluster ',num2str(un2use(e))],'Other Clusters')
end

%% Start analyzing data
%Initialize some variables
Fs = spikes.Fs;s2t = @(x) x./Fs; t2s = @(x) ceil(x*Fs); %Sampling rate and handle to go from samples to time and time to samples
ws = size(spikes.waveforms,2); %window size
jit = t2s(.5*.001); %This is some extra time to allowspike waveforms to be aligned to their peaks (This code doesn't align spike waveforms)
shw = spikes.shadow; %shadow in ms
outNames = fieldnames(spkB); %Get fieldnames from output structure
%Start...
disp(['Performing NTM on chosen mat files...', 'Window size for each channel: ',num2str(ws),' samples. Shadow: ',num2str(shw),'ms'])
disp(['Single units that will be used as templates: ',num2str(un2use)])
for e = 1:length(fname) %Loop over matfiles 
    %Allocate memory
    new_wave = cell(1,numU); %Allocate memory for waveforms
    triInd = new_wave; %row index (i.e. trial) of voltage matrix in which a spike was detected 
    timInd = new_wave; %column index (i.e. sample) of voltage matrix in which a spike was detected 
    disp(['Loading ',fname{e}((find(fname{e}=='\',1,'last')+1):end),'...'])
    data2use = load(fname{e}); %Load file to be analyzed
    %Check variables in mat file (there should only be one variable which
    %is a 2D or 3D matrix with voltage data!!)
    varsIn = fieldnames(data2use);
    if(length(varsIn)>1) %More than one variable in file
        error(['File ',fname{e},' has more than one variable stored. Chosen files must only have the voltage data matrix!'])
    end
    data2use = data2use.(varsIn{1});
    disp('loading successful')
    try
        data = data2use(:,:,chns);
    catch
        error('Channel indices are not consistent with the voltage data matrix')
    end
    data_new = nan(size(data,1),size(data,2),numU); %Cross-correlation of template with the data
    for hu = 1:numU %Loop over units (i.e. templates)
        temp2use = normA(reshape(templates(hu,:,:),1,[])); %template to use
        for hc = 1:(size(data,2)-ws-1) %compute cross-correlation
            crtD = reshape(data(:,hc:(hc+ws-1),:),size(data,1),[],1); %extract piece of data
            crtD = normA(crtD);
            data_new(:,hc) = sum(bsxfun(@times,crtD,temp2use),2); %compute "correlation" value and store
        end
        data_new2 = (data_new>=ClassT(hu));%Find threshold crossings
        [trial,smpl] = find(data_new2);%Get indices of threshold crossings  
        [trial,indx] = sort(trial); smpl=smpl(indx); smpl = mat2cell(smpl,histc(trial,1:size(data,1)),1); %Segregate by trial
        empI = cellfun('isempty',smpl); %Check if unit didn't spike in some trial
        smpl(~empI) = cellfun(@(x) mat2cell(x,diff([0;find([diff(x);1000]>t2s(shw*.001))]),1),smpl(~empI),'un',0); %This eliminates the problem of having the waveform cross threshold multiple times 
        temp = cell(length(smpl),1); %It will store waveforms for each sweep
        spk_times = temp;
        spk_trials = temp;
        for sw = 1:length(smpl) %Again loop over sweeps
            wvs2 = smpl{sw};
            if(~isempty(wvs2)) %Cell spikes
                wvs2 = cellfun(@(x) x(find(data_new(sw,x)==max(data_new(sw,x)),1)),wvs2); %get values were projection values are maxed
                %Check if any units spikes at a time smaller than
                %the jitter
                fst = wvs2<=jit;
                if(sum(fst)>0) %There are spikes that happened to early in the sweep
                    temp2 = cell(length(fst),1); temp2(fst) = arrayfun(@(x) data(sw,(x):(x+ws+jit-1),:),wvs2(fst),'un',0);
                    temp2(~fst) = arrayfun(@(x) data(sw,(x-jit):(x+ws-1),:),wvs2(~fst),'un',0); temp2 = vertcat(temp2{:});
                else
                    temp2 = arrayfun(@(x) data(sw,(x-jit):(x+ws-1),:),wvs2,'un',0); temp2 = vertcat(temp2{:});
                end
                    temp{sw}=temp2; 
                    spk_times{sw} = s2t(wvs2);
                    spk_trials{sw} = ones(length(wvs2),1).*sw;
             end
         end
         %Store data
         new_wave{1,hu}=vertcat(temp{:});
         timInd{1,hu} = vertcat(spk_times{:});
         triInd{1,hu} = vertcat(spk_trials{:});
    end
    %Check for spike repeats across units
    %Collapse across trials
    new_wave = vertcat(new_wave{:});
    triInd = vertcat(triInd{:});
    timInd = vertcat(timInd{:});
    %'unwrap' times (cumulative time instead of by trials)
    unwrp = s2t((triInd-1).*(size(data,2))) + timInd; %Assumes there's no time spacing between trials 
    [ut,indx] = sort(unwrp); %Sort unwrapped times 
    new_wave = new_wave(indx,:,:); triInd = triInd(indx); timInd = timInd(indx); %Sort according to unwrapped times
    %Apply shadow to remove repeats across units 
    tt2 = [false;diff(ut)<=(shw*.001)]; 
    new_wave(tt2,:,:)=[]; triInd(tt2)=[]; timInd(tt2)=[]; ut(tt2)=[]; %Delete spikes
    %Store data in output structure
    spkB.(outNames{e}).waveforms = new_wave; 
    spkB.(outNames{e}).trials = triInd;
    spkB.(outNames{e}).spiketimes = timInd;
    spkB.(outNames{e}).unwrapped_times = ut; 
end
    


end

