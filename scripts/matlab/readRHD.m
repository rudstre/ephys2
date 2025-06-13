function [ephys, acc, vdd, tmp, dio] = readRHD(fid, sampOffset, chunkSize, nelectrodes)
%sampOffset: where in file to begin reading (typically in loop to minize
%reading)
% ChunkSize: how many samples to read (default 100*10^6 samples)
%nelectrodes should be 64

%Outputs:
%dio is TTL
%vdd is voltage in that the chip is seeing
%tmp is chip temperatures 


nelectrodes =64;


foffset = floor(sampOffset/60)*60 * 88 * 2;
chunkSize = floor(chunkSize/60)*60;

if sampOffset ~= -1
    fseek(fid, foffset, 'bof');
end
%data has 88 channels for everything
% can use skip parameter on fread
dat = fread(fid, chunkSize*88, 'uint16');

%% can skip this if only want dio
ephys = zeros(nelectrodes, chunkSize);
acc = zeros(3, chunkSize/4);
vdd = zeros(2, chunkSize/60);
tmp = zeros(2, chunkSize/60);

for n = 1 : nelectrodes
   ephys(n,:) = dat(12+n : 88 : chunkSize*88);
end

ephys = (ephys([(1:2:nelectrodes) (2:2:nelectrodes)], :) - 32768) * 1.95e-7;

%% Can start here if only needing dio
dio = cast(dat(87:88:chunkSize*88), 'uint16');

for n = 1 : 3
   acc(n,:) = dat(n*88+10 : 88*4 : chunkSize*88);
end
acc = (acc - 32768)*3.74e-5;

vdd(1,:) = dat(28*88+8+1 : 60*88 : chunkSize*88);
vdd(2,:) = dat(28*88+8+2 : 60*88 : chunkSize*88);
vdd = vdd * 7.48e-5;

tmp(1,:) = dat(20*88+8+1 : 60*88 : chunkSize*88) - dat(12*88+8+1 : 60*88 : chunkSize*88);
tmp(2,:) = dat(20*88+8+2 : 60*88 : chunkSize*88) - dat(12*88+8+2 : 60*88 : chunkSize*88);
tmp = (tmp/98.9)-273.15;

