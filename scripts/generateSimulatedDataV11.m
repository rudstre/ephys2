function generateSimulatedDataV11(unitStruct, nUnits, recHours)
% Generate simulated spiking data by combining spike library with empty
% recording. Repeat empty recording to save on run time. Generate all spike
% Amps before adding them to recording. Include multiunit spike cluster.
% Start with uniform distribution of spike amplitudes.
% Upper bound on amplitude of random walk set independently for each unit
% based on expoential distribution.

[WVs, FRs, Amps, ~, unitNums] = makeAutoWvLibrary(unitStruct);

%%
recLength = recHours * 3600; % Input in hours, convert to sec
nsamp = 64;
resamp = 10;
psamp = 32;
samprate = 3e4;

minAmp = 1e-4;
acptrPath = '\\140.247.178.8\asheshdhawale\Data\Bhimpalasi\635132850023415351';
acptrTet = 15; % 1 indexed
acptrMedFile = 'Ref1'; % for median filtering

nTet = length(nUnits); % number of tetrodes to simulate (MUST BE <= 6 !!)
writeTets = [1:4; 5:8; 9:12; 33:36; 37:40; 41:44]; % Split tets between chips (max 6 tets)
writeTets = writeTets(1:nTet, :);

fracInt = 0.2; % fraction of neurons that are interneurons
prinType = 1;
intType = 2;

% Background multiunit activity
b_nUnits = 40;
b_uFR = 20; % overall multiunit firing rate in Hz
b_mAmp = -50e-6; % mean of background amp distribution
b_sdAmp = 25e-6; % standard deviation of amp distribution

% fname = 'small_drift';
targPath = '\\140.247.178.65\asheshdhawale\Data\SimulatedData\';
if exist(targPath, 'dir') ~= 7
    mkdir(targPath);
end

%% Filter out low amplitude units

% highAmpU = any(abs(Amps) >= minAmp, 2);
highAmpU = any(Amps <= -minAmp, 2);
WVs = WVs(highAmpU,:,:);
FRs = FRs(highAmpU);
Amps = Amps(highAmpU,:);
unitNums = unitNums(highAmpU);
prinInd = find([unitStruct(unitNums).unitType] == prinType);
intInd = find([unitStruct(unitNums).unitType] == intType);

%% Pick nTet sets of nUnits

uind = cell(nTet,1);
for tet = 1 : nTet
    uind{tet} = zeros(1,nUnits(tet));
    
    if fracInt ~= 0
        nInt = max([1, round(fracInt*nUnits(tet))]);
        % Pick principal neurons
        uind{tet}(1:(nUnits(tet)-nInt)) = prinInd(randperm(length(prinInd), nUnits(tet)-nInt));
        % Pick interneurons
        uind{tet}((end-nInt+1):end) = intInd(randperm(length(intInd), nInt));
    else
        % Pick principal neurons
        uind{tet}(1:nUnits(tet)) = prinInd(randperm(length(prinInd), nUnits(tet)));
    end    

    % Plot selected waveforms
    figure(1);
    subplot(ceil(nTet/floor(sqrt(nTet))), floor(sqrt(nTet)), tet);
    plotWVs = WVs(uind{tet}(:),:,:) .* abs(repmat(Amps(uind{tet}(:),:),1,1,size(WVs,3)));
    plot(reshape(permute(plotWVs, [1 3 2]), nUnits(tet), numel(plotWVs(1,:,:)))');

    figure(1+tet);
    icount=1;
    for ch1 = 1:3
        for ch2 = ch1+1:4
            subplot(3,2,icount);
            plot(randn(1000,1)*1e-5, randn(1000,1)*1e-5, 'k.'); % plot noise
            hold on;
            for u = 1 : nUnits(tet)
                plot(randn(1000,1)*1e-5+Amps(uind{tet}(u),ch1), randn(1000,1)*1e-5+Amps(uind{tet}(u),ch2),'.'); 
            end
            hold off;
            icount=icount+1;
        end
    end
end

%% Get unit waveforms and firing rates

uAmps = cell(nTet,1);
uFRs = cell(nTet,1);
uNums = cell(nTet,1);
for tet = 1 : nTet
    uAmps{tet} = Amps(uind{tet},:);
    uFRs{tet} = FRs(uind{tet});
    uNums{tet} = unitNums(uind{tet});
end

% uFRs = repmat(logspace(log10(minFR), log10(maxFR), nUnits), nTet, 1); % log spaced firing rates from min to max FR
% uFRs = logspace(log10(minFR), log10(maxFR), nUnits);

tWV = ((1:nsamp) - psamp)/samprate;
tWV_r = (tWV(1)-1/samprate/2): 1/(samprate*resamp) : (tWV(end)+1/samprate/2);

uWVs = cell(nTet,1);
for tet = 1 : nTet
    uWVs{tet} = zeros(nUnits(tet), size(WVs,2), length(tWV_r));
    % Sub-sample waveforms
    for u = 1 : nUnits(tet)
        uWVs{tet}(u,:,:) = interp1(tWV, squeeze(WVs(uind{tet}(u),:,:))', tWV_r, 'pchip')';    
    end
    % Remove waveforms offset
    uWVs{tet} = uWVs{tet} - repmat(mean(uWVs{tet}(:,:,1:100),3), 1, 1, size(uWVs{tet},3));
end

%% Pick background units

b_uind = randperm(length(unitNums),b_nUnits);

% Plot selected waveforms
figure;
plotWVs = WVs(b_uind(:),:,:);
plot(reshape(permute(plotWVs, [1 3 2]), b_nUnits, numel(plotWVs(1,:,:)))');
title('Background waveforms');

b_uNums = unitNums(b_uind);

% Resample background waveforms
b_uWVs = zeros(b_nUnits, size(WVs,2), length(tWV_r));

for bu = 1 : b_nUnits
    b_uWVs(bu,:,:) = interp1(tWV, squeeze(WVs(b_uind(bu),:,:))', tWV_r, 'pchip')'; 
end

% Remove waveforms offset
b_uWVs = b_uWVs - repmat(mean(b_uWVs(:,:,1:100),3), 1, 1, size(b_uWVs,3));

%% Generate spike times for units

% Different spike times for each tetrode
sp = cell(nTet,1);
sp_u = cell(nTet,1);
for tet = 1 : nTet
    disp(['Tet ' num2str(tet)]);
    this_sp = [];
    this_sp_u = [];
    for u = 1 : nUnits(tet)
        usp = generateSpikeTimes(uFRs{tet}(u), recLength, 2e-3) * samprate;
        usp = usp(usp > psamp & usp < (recLength*samprate)-psamp);
        this_sp = [this_sp, usp];
        this_sp_u = [this_sp_u, zeros(size(usp))+u];
    end
    [this_sp, I] = sort(this_sp);
    this_sp_u = this_sp_u(I);
    
    sp{tet} = this_sp;
    sp_u{tet} = this_sp_u;
    clear usp this_sp this_sp_u;
end

b_sp = generateSpikeTimes(b_uFR, recLength, 1e-5) * samprate;
b_sp = b_sp(b_sp > psamp & b_sp < (recLength*samprate)-psamp);
b_sp_u = ceil(rand(size(b_sp)) * b_nUnits);

%% Determine frequency of overlaps for each tetrode and each unit

t_match = 16;
foverlaps = cell(nTet,1);
for tet = 1 : nTet
    foverlaps{tet} = zeros(nUnits(tet),1);
    for n = 1 : nUnits(tet)
        foverlaps{tet}(n) = sum(((sp_u{tet}(1:end-1) == n) & (diff(sp{tet}) < t_match)) | ((sp_u{tet}(2:end) == n) & (diff(sp{tet}) < t_match))) / sum((sp_u{tet} == n));        
    end
end

%% Generate waveform traces superimposed onto noise trace

% Params
amp_Snoise = 0.1; % Signal dependent noise factor 
amp_drift = [1e-6]; % exp drift (variance) per sec
fnames = {'med_drift17'};  

% Set bounds
% bounds = [-75e-6; -300e-6]; % boundaries for random walk (same for every unit)
% bounds = repmat(bounds, 1, 4);

% Different upper boundaries for every unit - exponentially distributed

lower_bound = -75e-6;

upbound_exp = 2e-4;
upbound_range = 150e-6 : 1e-6 : 400e-6;
upbound_cdf = expcdf(upbound_range, upbound_exp);
upbound_cdf = (upbound_cdf - min(upbound_cdf))/(max(upbound_cdf) - min(upbound_cdf)); % normalize cdf to fall between 0 and 1 for amp_distr range
upper_bound = cell(nTet,1);
for tet = 1 : nTet
    upper_bound{tet} = -arrayfun(@(x) upbound_range(find(upbound_cdf <= x, 1, 'last')), rand(nUnits(tet), 4)); % independent bound for each tetrode channel    
%     upper_bound{tet} = repmat(-arrayfun(@(x) upbound_range(find(upbound_cdf <= x, 1, 'last')), rand(nUnits(tet), 1)), 1, 4); % same bound for each tetrode channel    
end

% Divide input data into chunks for reading and processing
chunkSize = 5e7;
nchunks = ceil(recLength*samprate/(chunkSize));

%%
for a = 1 : length(amp_drift)    
    %% 
    disp(fnames{a});
    
    % Initialize arrays
    
    d_Amps = cell(nTet,1); % for visualization of amp drifts 
    
    this_amp_drift = amp_drift(a);
        
    % Generate Amps
    disp('Generating Amps');
    for tet = 1 : nTet
        disp(['Tet ' num2str(tet)]);
        last_sp = zeros(nUnits(tet),1);
        d_Amps{tet} = zeros(length(sp{tet}),4);
        norm_rnd = randn(length(sp{tet}),4,2);
%         m_Amps = uAmps{tet};
        
        % Start with Amps uniformly distributed between their respective bounds
        m_Amps = (rand(nUnits(tet),4) .* (upper_bound{tet} - lower_bound)) + lower_bound;
        uAmps{tet} = m_Amps;
        
        for n = 1 : length(sp{tet})
            if n/2000000 == fix(n/2000000); disp(n/length(sp{tet})); end
            nextAmp = squeeze(m_Amps(sp_u{tet}(n),:)) .* exp(sqrt(this_amp_drift * ((sp{tet}(n)-last_sp(sp_u{tet}(n)))/samprate)) * squeeze(norm_rnd(n,:,1)));
%             nextAmp = max([nextAmp; bounds(2,:)]); % don't exceed maximum Amp
%             nextAmp = min([nextAmp; bounds(1,:)]);  % don't dip below minimum Amp

%             upper_ind = nextAmp < upper_bound{tet}(sp_u{tet}(n),:); % index of nextAmps violating upper boundary
%             nextAmp(upper_ind) = 2*upper_bound{tet}(sp_u{tet}(n),upper_ind) - nextAmp(upper_ind); % reflecting upper boundary
%             nextAmp(nextAmp > lower_bound) = 2*lower_bound - nextAmp(nextAmp > lower_bound); % reflecting lower boundary

            nextAmp = max([nextAmp; upper_bound{tet}(sp_u{tet}(n),:)]); % buffering upper boundary
            nextAmp = min([nextAmp; repmat(lower_bound,1,4)]); % buffering lower boundary
        
            % Update mean amps based on geometric random walk model
            m_Amps(sp_u{tet}(n),:) = nextAmp;
            
            % Add signal dependent noise to amp
            d_Amps{tet}(n,:) = squeeze(m_Amps(sp_u{tet}(n),:)) + (squeeze(abs(m_Amps(sp_u{tet}(n),:))) .* amp_Snoise .* squeeze(norm_rnd(n,:,2)));
            
            % Update last spike time for this unit
            last_sp(sp_u{tet}(n)) = sp{tet}(n); 
        end
        
        clear norm_rnd;
    end
    
    % Generate background amps
    b_Amps = (randn(length(b_sp), 4) * b_sdAmp) + b_mAmp;
    
    save([targPath fnames{a} '_' num2str(uint16(recLength/3600)) 'h.mat'], 'sp', 'sp_u', 'd_Amps', 'uWVs', 'uFRs', 'uAmps', ...
        'amp_Snoise', 'this_amp_drift', 'uNums', 'acptrPath', 'acptrTet', 'writeTets','nUnits','upper_bound', 'lower_bound',...
        'upbound_exp', 'upbound_range', 'b_Amps', 'b_sp', 'b_sp_u', 'b_sdAmp', 'b_mAmp', 'b_nUnits', 'b_uFR', 'b_uWVs', ...
        'b_uNums', '-v7.3');
    
    %% Plot simulation results (optional)
 
    skip=100;
    for tet = 1 : nTet
        figure(2+tet);
        icount=1;
        for ch1 = 1:3
            for ch2 = ch1+1:4
                subplot(3,2,icount);
                scatter3(b_sp(1:skip:end)/samprate, squeeze(b_Amps(1:skip:end,ch1)), squeeze(b_Amps(1:skip:end,ch2)), 'k.');
                hold on;
                for u = 1 : nUnits(tet)
                    usp_ind = find(sp_u{tet} == u);
                    scatter3(sp{tet}(usp_ind(1:skip:end))/samprate, squeeze(d_Amps{tet}(usp_ind(1:skip:end),ch1)), squeeze(d_Amps{tet}(usp_ind(1:skip:end),ch2)),'.');                     
                end
                xlabel(['Ch ' num2str(ch1)]); ylabel(['Ch ' num2str(ch2)]); 
                hold off;
                icount=icount+1;
                title(['Tet ' num2str(tet)]);
            end
        end
    end
        
    %% Write WVs to file
    
    wfid = fopen([targPath fnames{a} '_' num2str(uint16(recLength/3600)) 'h.amp'], 'w', 'l'); % for 16 tets
    for c = 1 : nchunks
        if c/30 == fix(c/30); disp(c/nchunks); end
        
        if c == 1
            disp('Reading acceptor data');
            
            % Read in median data
            medfid = fopen([acptrPath '\' acptrMedFile], 'r', 'l');
            med = fread(medfid, [1, chunkSize], 'int16=>int16');
            fclose(medfid);
            med = uint16(double(med) + 32768);
            
            % Read in acceptor data
            ampfid = fopen([acptrPath '.amp'], 'r', 'l');
            acptrData = fread(ampfid, [64, chunkSize], 'uint16=>uint16');
            fclose(ampfid);
            acptrData = acptrData((acptrTet-1)*4+1:acptrTet*4, :);  
            
            disp('Writing amp file...');
        end

        % Get rid of spikes half-waveform away from the edges
        for tet = 1 : nTet
            no_sp = abs(sp{tet} - chunkSize*(c-1)) <= psamp | abs(sp{tet} - chunkSize*(c)) <= psamp;
            sp{tet}(no_sp) = [];
            sp_u{tet}(no_sp) = [];
            d_Amps{tet}(no_sp,:) = [];
        end
        
        % Get rid of bg spikes half-waveform away from the edges
        b_no_sp = abs(b_sp - chunkSize*(c-1)) <= psamp | abs(b_sp - chunkSize*(c)) <= psamp;
        b_sp(b_no_sp) = [];
        b_sp_u(b_no_sp) = [];
        b_Amps(b_no_sp,:) = [];

        % Find relevant spike times and their closest samples in data
        sp_ind = cell(nTet,1);
        sp_samp = cell(nTet,1);
        for tet = 1 : nTet
            sp_ind{tet} = find(sp{tet} >= chunkSize*(c-1) & sp{tet} < chunkSize*c);
            [~, sp_samp{tet}] = histc(sp{tet}(sp_ind{tet}), chunkSize*(c-1)+0.5 : 1 : (chunkSize*c)-0.5);
        end
        
        % Find relevant background spike times and their closest samples in
        % data
        b_sp_ind = find(b_sp >= chunkSize*(c-1) & b_sp < chunkSize*c);
        [~, b_sp_samp] = histc(b_sp(b_sp_ind), chunkSize*(c-1)+0.5 : 1 : (chunkSize*c)-0.5);
        
        % Generate dummy data for other tetrodes
%         writeData = [acptrMedData; zeros(32, size(acptrData,2), 'uint16')+32768];
        writeData = repmat(med, 64, 1);
                
        % Generate simulated data for each tetrode
        for tet = 1 : nTet
            tetData = double(acptrData) - 32768;
            
            %% Loop through spikes to generate simulated data
            for x = 1 : length(sp_ind{tet})        
                n = sp_ind{tet}(x); % n is the index into the full sp vector
                
                this_amp = d_Amps{tet}(n,:);

                % Scale waveform by amp
                this_wv = squeeze(uWVs{tet}(sp_u{tet}(n),:,:)) .* repmat(abs(this_amp(:)), 1, length(tWV_r));

                % Relative time for spike
                t_sp = tWV - (sp{tet}(n) - (sp_samp{tet}(x)+chunkSize*(c-1)))/samprate;

                % Resample waveform
                this_wv = interp1(tWV_r, this_wv', t_sp)';
                this_wv = this_wv/1.95e-7;

                tetData(:,(sp_samp{tet}(x)-psamp+1) : sp_samp{tet}(x)+psamp) = tetData(:,(sp_samp{tet}(x)-psamp+1) : sp_samp{tet}(x)+psamp) + this_wv;           
            end
            
            %% Add background spikes
            for x = 1 : length(b_sp_ind)        
                n = b_sp_ind(x); % n is the index into the full b_sp vector
                
                this_amp = b_Amps(n,:);

                % Scale waveform by amp
                this_wv = squeeze(b_uWVs(b_sp_u(n),:,:)) .* repmat(abs(this_amp(:)), 1, length(tWV_r));

                % Relative time for spike
                t_sp = tWV - (b_sp(n) - (b_sp_samp(x)+chunkSize*(c-1)))/samprate;

                % Resample waveform
                this_wv = interp1(tWV_r, this_wv', t_sp)';
                this_wv = this_wv/1.95e-7;

                tetData(:,(b_sp_samp(x)-psamp+1) : b_sp_samp(x)+psamp) = tetData(:,(b_sp_samp(x)-psamp+1) : b_sp_samp(x)+psamp) + this_wv;           
            end
            
            
            %%
            writeData(writeTets(tet,:),:) = uint16(tetData + 32768);
            clear tetData;
        end
        
        % Store in correct order (chip1 and chip2 channels interleaved; may need to change when snippeting is fixed for amp files)
        chipInd = [1:32; 33:64];
        writeData = writeData(chipInd(:),:);
        
        % Write hybrid data to disk
        fwrite(wfid, writeData(:), 'uint16');
        clear writeData;
    end
    fclose(wfid);
    clear med actprData;
    save([targPath fnames{a} '_' num2str(uint16(recLength/3600)) 'h.mat'], 'd_Amps', 'sp', 'sp_u', 'b_Amps', 'b_sp', 'b_sp_u', '-v7.3', '-append');

end

