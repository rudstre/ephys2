function [WVs, FRs, Amps, plotWVs, unitNums] = makeAutoWvLibrary(unitStruct)

nsamp = 64;
nCh=4;
WVs = zeros(length(unitStruct), nCh, nsamp);
Amps = zeros(length(unitStruct), nCh);
FRs = zeros(length(unitStruct),1)*NaN;

for u = 1 : length(unitStruct)    
    counts = zeros(2,1);
    wv = zeros(2,4,nsamp);
    wv_g = zeros(2,4,nsamp);
    for c = 1 : size(unitStruct(u).wv,1)
        thiswv = unitStruct(u).wv{c,1} * 1.95e-7;
        wvnum = unitStruct(u).wv{c,2};
        
        if numel(unitStruct(u).wv{c,2}) > 1            
            counts = counts + wvnum;
            wv = wv + (thiswv .* repmat(wvnum,1,size(thiswv,2),size(thiswv,3))); % arithmetic mean
            wv_g = wv_g + (log(abs(thiswv)) .* repmat(wvnum,1,size(thiswv,2),size(thiswv,3))); % geometric mean
        else
            if abs(min(min(squeeze(thiswv)))) > abs(max(max(squeeze(thiswv))))
                wv(1,:,:) = wv(1,:,:) + (thiswv .* repmat(wvnum,1,size(thiswv,2),size(thiswv,3))); % arithmetic mean
                wv_g(1,:,:) = wv_g(1,:,:) + (log(abs(thiswv)) .* repmat(wvnum,1,size(thiswv,2),size(thiswv,3))); % geometric mean
                counts(1) = counts(1) + wvnum;
            else
                wv(2,:,:) = wv(2,:,:) + (thiswv .* repmat(wvnum,1,size(thiswv,2),size(thiswv,3))); % arithmetic mean
                wv_g(2,:,:) = wv_g(2,:,:) + (log(abs(thiswv)) .* repmat(wvnum,1,size(thiswv,2),size(thiswv,3))); % geometric mean
                counts(2) = counts(2) + wvnum;
            end
        end        
    end
    [max_count, max_ind] = max(counts);
    this_wv = wv(max_ind,:,:)/max_count; % arithmetic mean
    this_wv_g = exp(wv_g(max_ind,:,:)/max_count);
    if max_ind == 1
%         [~,i] = min(this_wv, [], 3);
%         this_amp = -this_wv_g(sub2ind(size(this_wv_g), [1,1,1,1], [1,2,3,4], i));
        this_amp = min(this_wv,[],3);
    else
%         [~,i] = max(this_wv, [], 3);
%         this_amp = this_wv_g(sub2ind(size(this_wv_g), [1,1,1,1], [1,2,3,4], i));
        this_amp = max(this_wv,[],3);
    end
    if isfield(unitStruct, 'avgFR')
        FRs(u) = unitStruct(u).avgFR;
    end
    WVs(u,:,:) = this_wv ./ repmat(abs(this_amp), 1, 1, nsamp);
    Amps(u,:) = this_amp;
end

for u = 1 : length(unitStruct)
    for ch = 1 : nCh
        if all(WVs(u,ch,:) == 0); WVs(u,ch,:) = NaN; end
    end
end

plotWVs = reshape(permute(WVs, [1 3 2]),  size(WVs,1), numel(WVs(1,:,:)));

% Get rid of units with missing channels and poor normalization
WVs = WVs(~any(isnan(plotWVs) | abs(plotWVs) > 1.1, 2),:,:);
FRs = FRs(~any(isnan(plotWVs) | abs(plotWVs) > 1.1, 2));
unitNums = find(~any(isnan(plotWVs) | abs(plotWVs) > 1.1, 2));
Amps = Amps(~any(isnan(plotWVs) | abs(plotWVs) > 1.1, 2), :);
plotWVs = plotWVs(~any(isnan(plotWVs) | abs(plotWVs) > 1.1, 2),:);
