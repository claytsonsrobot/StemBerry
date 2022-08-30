% Title: SOCEM2021_dataCompilation_v2.m
% Author: Clayton Bennett
% Created: 16 March 2022
% Last edited: 16 March 2022
%
% Purpose:
% - Import any xlsx file!! Expect a single row for single values. Any
% columns longer than 1 row will be imported as a cells.
% - Checks that the filename is present as a data column. If not, two
% columns will be added, one for the short name and one for the entire file
% location.

% SOCEM specific:
% - Pull in data from analyzed SOCEM files, in "EI, Analyzed" and "EI,
%      Analyzed_timebased" folders.
% - This data does not include things like run numbers and hour label,
% though these are discernible from description and filename text.
savestuff = 'y';
format compact
%% Import data
% Edit this section for your specific needs.
% names key folders

directory_script = ''; % ENTER script location
dir_compiledData = ''; % ENTER target file directory

if (directory_script(end)~='\')
    directory_script = strcat(directory_script,'\');
end

% folders for dividing up the 2021 data
level1names = {'August5','August6','August10','August13'};
%level1names = {'August28'};
%level1names = {'correctedHeights'}
level2names = {'EI_outputFiles'}; % Use both of these?
%level2names = {'cleanRaw'}; % Use both of these?
list_xlsxfiles = {};

for i_level1name = 1:numel(level1names) % i_level1name=4;
    for j_level2name = 1:numel(level2names) % j_level2name=1;
        activefolder = strcat(directory_data,level1names{i_level1name},'\',level2names{j_level2name},'\');
        cd(activefolder)
        % files files in active folder, then remove files that are not of the
        % proper filetype
        desired_import_filetype = '.xlsx';
        list_xlsxfiles_active = strtrim(string(ls())); %string(ls()) % cellstr(ls())
        
        i=1;
        while i<=numel(list_xlsxfiles_active)
            if not(contains(list_xlsxfiles_active(i),desired_import_filetype))
                list_xlsxfiles_active(i)=[];
            else
                list_xlsxfiles_active(i) = strcat(activefolder,list_xlsxfiles_active(i));
                i=i+1;
            end
        end
        
        for i=1:numel(list_xlsxfiles_active)
            list_xlsxfiles{end+1}=list_xlsxfiles_active(i);
        end
    end % end level 1 names loop
end % end level 2 names loop
n_files = numel(list_xlsxfiles);

%% Import data from each file
% Look one column at a time. Record the column header name. If the column
% is greater than one row long, package it as a cell

% Some numeric data saved by python was output as string. Find which.
stringToDouble=[];
cellTrack=[];
list_filepath= {};
list_filedetail = {};


handle_waitbar=waitbar(0,strcat('Data is being imported from ',string(n_files),' SOCEM files. Computer speed, go!'));
for i=1:n_files
    
    filename = list_xlsxfiles{i};
    strfile=filename;
    sheets = sheetnames(strfile);
    
    [filepath,filedetail,ext] = fileparts(filename);
    list_filepath{end+1} = filepath;
    list_filedetail{end+1} = filedetail;
    
    T_active = [];
    for s = 1:numel(sheets) % loop through all sheets in the same file
    if s>1
        opts_sheetPrevious = opts_sheet;
    end
    
    opts_sheet = detectImportOptions(strfile,'Sheet',sheets{s},'PreserveVariableNames',1);
    
    % Remove duplicates from sheet 2 and above, if they data has been
    % represented in a previous sheet.
    if s>1
        % find duplicates, to remove from second sheet
        k=1;
        while k<=numel(opts_sheet.VariableNames)
            if sum(opts_sheet.VariableNames{k}==string(opts_sheetPrevious.VariableNames))>0
                opts_sheet.VariableNames(k)=[];
            else
                k=k+1;
            end
        end
    end
    
    charIdx=string(opts_sheet.VariableTypes)=='char';
    charNames=opts_sheet.VariableNames(charIdx);
    opts_sheet=setvartype(opts_sheet,charNames,'string');
    

    %create table
    T_active_sheet = table('Size',[size(opts_sheet.VariableNames)],'VariableNames',opts_sheet.VariableNames,'VariableTypes',opts_sheet.VariableTypes);

    % get raw data
    t_active_sheet = readtable(filename,opts_sheet,'Sheet',sheets{s});

    % allocate raw data into a single row for active sheet
    for k = 1:width(t_active_sheet)
        columnData=rmmissing(t_active_sheet.(k));
        if isempty(columnData)
            if sum(cellTrack==k)>0
                columnData = [];
                T_active_sheet.(k)={columnData};
            elseif sum(cellTrack==k)==0 && sum(stringToDouble==k)>0
                columnData = NaN;
                T_active_sheet.(k)=columnData;
            end
        elseif numel(columnData)>1
            if isstring(columnData) && logical(mean(not(isnan(double(columnData)))))
                columnData = double(columnData);
                if sum(stringToDouble==k)==0
                    stringToDouble(end+1)=k;
                end
                
            end
            
            if sum(cellTrack==k)==0
                cellTrack(end+1)=k;
            end
            T_active_sheet.(k)={columnData};
        elseif numel(columnData)==1
            if isstring(columnData) && not(isnan(double(columnData))) % some numeric data was saved by python as a string. This fixes it.
                columnData = double(columnData);
                if sum(stringToDouble==k)==0
                    stringToDouble(end+1)=k;
                end
            end
            T_active_sheet.(k)=columnData;
        end
    end
    
    
    T_active = [T_active,T_active_sheet];
    
    end % loop through all sheets in the same file
    % Once all sheets have been imported,
    % check to see if filename was stored in the table, in final row.
    % If not, add filepath and filedetail.
    if i==1
        hay_filedetail = 0;
        for checkcolumn = 1:width(T_active)
            if isstring(table2array(T_active(end,checkcolumn))) || ischar(table2array(T_active(end,checkcolumn)))
                if 1==numel(table2array(T_active(end,checkcolumn)))
                    if contains(table2array(T_active(end,checkcolumn)),filedetail)
                        hay_filedetail = 1; % "hay" is spanish for "there is". "1" is binary for "yes, there is".
                        break % leave this for loop, what is sought has been found
                    else
                        hay_filedetail = -99; % to show that the first row was already checked
                    end
                else 
                    hay_filedetail = -98;
                end
            else hay_filedetail = -97;
            end
        end
    end
    % if hay_filedetail is still zero, and no record of the filename was
    % found, then record the full filename and the file detail, in two new
    % columns.
    if not(hay_filedetail == 1) % file name details were not found in the first row of the table. Beware of mixed directories with files from various stages of development.
        T_active.("File detail") = filedetail;
        T_active.Filename = filename; 
    end
    
    
    if i==1
        T = T_active;
    elseif string(T.Properties.VariableNames)==string(T_active.Properties.VariableNames)
        T = [T;T_active];
    else % different variable names, different number of columns
        msg= strcat("Your files have columns that differ.", newline(), filename);
        disp(msg)
        % In this case, items are not stored?
        % if class(string), use <missing>
        % if class(double), use NaN
        % if other, use ....?
    end
    
    fprintf('%d.', i)
    waitbar(i/n_files,handle_waitbar)
    
end

% If file details were just added because they weren't present in the
% imported data, put the filedetail column first, so that it's easy to read. 
if not(hay_filedetail==1)
    T = [T(:,end-1), T(:,1:end-2) ,T(:,end)];
end

close(handle_waitbar)
fprintf('\n')
cd(directory_script)

%% prep for CSV, remove columns with cells
Tcsv=T;
[rows,cols]=size(T);
c=1;
while c<=cols
    if string(class(Tcsv.(c)))==string('cell')
        Tcsv.(c)=[];
    else
        c=c+1;
        
    end
    [rows,cols]=size(Tcsv);
end

%% CSV creation

filename_detail = 'wheat2021_SOCEM_directImport';
filenameCSV_withCells = strcat('T_',filename_detail,'_withCells_',cell2mat(level1names),'_',cell2mat(level2names),'_',date,'.csv');
filenameCSV = strcat('T_',filename_detail,'_',cell2mat(level1names),'_',cell2mat(level2names),'_',date,'.csv');

if savestuff == 'y'
cd(dir_compiledData)
writetable(T,filenameCSV_withCells,'FileType','Text','WriteVariableNames',1);
writetable(Tcsv,filenameCSV,'FileType','Text','WriteVariableNames',1);
end
cd(directory_script)

