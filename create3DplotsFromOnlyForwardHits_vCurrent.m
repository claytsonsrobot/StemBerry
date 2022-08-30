% title: create3DplotsFromOnlyForwardHits.m
% derived from: Compare_August13sideHits_to_StandardData_SW.m
% author: Clayton Bennett
% created: April 26, 2022


% Purpose:
% - Create 3D visuals, plots, STL's from only forward hits.
% - Implement artifical side hit assumptions.

% Important notes:
% - If T comes from a cleanRaw folder, rather than a EI_processed folder,
% the entire push will be displayed, including edge effect zones and any
% chaff-impregnated back-end that was tested. Mind your T's.


% Develop:
% - For the Y axis, check and see if these numbers are within range:
% [20:20:520]. If they are, generate them are a shape and extrude,
% alongside a shaped-set of tickmarks. This will exist offset, to the left
% of X=0.
% - For the X axis, do the same thing. Within the range of [0:20:120].
% These numbers have no bearing for units, and will function for current
% inches and future centimeters. Is auto-scaling necessary?
%
format compact
dir_compiledData = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Data - Instron and SOCEM\Compiled Data, Backups 2021 - mat, csv, xlsx, txt\';
dir_code = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Code - Matlab, Python, etc\Code - Matlab - Data Compilation\';
dir_saveImages = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Images, Figures, Graphs, Plots, Charts\Wheat 2021\SOCEM\August23_SideHits_PostRainSW\';
%file_data  = 'T_S_SOCEM_Wheat2021_August23_S_versus_August13_T.mat';
dir_tools_downloaded = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Code - Matlab, Python, etc\Code - Matlab - Data Compilation\DownloadedUtilites\';
dir_tools_homemade = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Code - Matlab, Python, etc\Code - Matlab - Data Compilation\Utilities\';

cd(dir_compiledData)
%load(file_data) % import data
load('colormat.mat')
cd(dir_code)

%% 3D plotting
cd(dir_code)
overwritestuff = 'n'; % edit switch here
dimcellSide = 210; % 315 % use one of these: 210, 315, 420, 525, 630, 735, 840
dimcellForward = dimcellSide;

for i=1:height(T)
%i=13;
forwardDistance = cell2mat(T.("Distance (in)")(i));
try
    forwardForce = cell2mat(T.("Force/row (lbs)")(i)).*T.("Rows")(i);
    sourceT = 'raw';
catch
    try
        forwardForce = cell2mat(T.("Force (lbs.)")(i));
        sourceT = 'processed';
    catch
        msg = "Expected column name was inaccurate. Stop. Help. Feed me."
        break
    end
end

try close(s)
end
hold off

X_append = [];
Y_append = [];
mat3D_append = [];
mat3D_append_floor = [];
X_append_combo = [];
Y_append_combo = [];
mat3D_append_combo = [];

% Create each side hit 3D object
for dave = 1:numel(k_list) 
    k = k_list(dave);
    if not(isnan(k))
        j=j_list(k);
        iA = iA_list(k);
        iB = iB_list(k);
        rangestart = rangestart_list_keep(k);
        rangeend = rangeend_list_keep(k);
    
    if go_list(k)==1
        kdo=kdo+1;
        sideForce = cell2mat(S.("Force/row (lbs)")(j));
        sideDistance = cell2mat(S.("Distance (in)")(j));
        
        D=zeros(3,1);
        D([1,2,3])=S.("x of force peak (in.)"){j}-min(sideDistance);
        
        sideDistance = 
        sideTime = 
        
        forwardForceRange = forwardForce(iA:iB);
        forwardDistanceRange = forwardDistance(iA:iB);
        
        peaks=S.("Force peaks at x (lbs.)"){j};
        
        iPeak=[0 0 0];
        for e = 1:3
            o = 1;
            while D(e)>sideDistance(o)
                
                o=o+1;
            end
            iPeak(e)= o ;
        end
        
        iValley = [0 0];
        sideForce_snip_peak1toPeak2 = sideForce(iPeak(1):iPeak(2));
        sideForce_snip_peak2toPeak3 = sideForce(iPeak(2):iPeak(3));
        numelBeforePeak1 = iPeak(1);
        numelBeforePeak2 = iPeak(2);
        
        % this sucks and needs to be fixed CB 04252022
        iValley(1) = min(find(sideForce_snip_peak1toPeak2==min(sideForce_snip_peak1toPeak2)))+numelBeforePeak1;
        iValley(2) = min(find(sideForce_snip_peak2toPeak3==min(sideForce_snip_peak2toPeak3)))+numelBeforePeak2;
        
        sideForce_snip_valley1toPeak2 = sideForce(iValley(1):iPeak(2));
        sideForce_snip_valley2toPeak3 = sideForce(iValley(2):iPeak(3));
        
        sideForce_snip_0toValley1 = sideForce(1:iValley(1));
        sideForce_snip_valley1toValley2 = sideForce(iValley(1):iValley(2));
        sideForce_snip_valley2toValley3 = sideForce(iValley(2):end);
        
        sideDistance_snip_0toValley1 = sideDistance(1:iValley(1));
        sideDistance_snip_valley1toValley2 = sideDistance(iValley(1):iValley(2));
        sideDistance_snip_valley2toValley3 = sideDistance(iValley(2):end);
        
        %calculate the area under the curve for each row
        areaRow = [0 0 0];
        areaRow(1) = trapz(sideDistance_snip_0toValley1,sideForce_snip_0toValley1);
        areaRow(2) = trapz(sideDistance_snip_valley1toValley2,sideForce_snip_valley1toValley2);
        areaRow(3) = trapz(sideDistance_snip_valley2toValley3,sideForce_snip_valley2toValley3);
     
        squareDistance = [0 0; 0 0; 0 0];
        squareDistanceDelta = [0 0 0];
        squareDistance(1,:) = [min(sideDistance_snip_0toValley1),max(sideDistance_snip_0toValley1)];
        squareDistance(2,:) = [min(sideDistance_snip_valley1toValley2),max(sideDistance_snip_valley1toValley2)];
        squareDistance(3,:) = [min(sideDistance_snip_valley2toValley3),max(sideDistance_snip_valley2toValley3)];
        
        squareDistanceDelta(1) = squareDistance(1,2)-squareDistance(1,1);
        squareDistanceDelta(2) = squareDistance(2,2)-squareDistance(2,1);
        squareDistanceDelta(3) = squareDistance(3,2)-squareDistance(3,1);
        
        squareForce = areaRow./(squareDistanceDelta./2);
        squareForce = peaks'; % overwrite, don't use area heights,because area width can be wrong
        
        valleys = [sideForce(1),[sideForce(iValley)]',sideForce(end)];
        
        sideForce_snip_peak1toMin12 = sideForce(iPeak(1):iValley(1));
        sideForce_snip_peak2toMin23 = sideForce(iPeak(2):iValley(2));
        sideForce_snip_peak3toEnd = sideForce(iPeak(3):numel(sideForce));
        
        iSquareA = [1,iValley];
        iSquareB = [iPeak];
        xSquareForm1 = [sideDistance(iSquareA(1)),sideDistance(iSquareA(1)),sideDistance(iSquareB(1)),sideDistance(iSquareB(1))];
        xSquareForm2 = [sideDistance(iSquareA(2)),sideDistance(iSquareA(2)),sideDistance(iSquareB(2)),sideDistance(iSquareB(2))];
        xSquareForm3 = [sideDistance(iSquareA(3)),sideDistance(iSquareA(3)),sideDistance(iSquareB(3)),sideDistance(iSquareB(3))];
        sideDistance_squareForm = [xSquareForm1,xSquareForm2,xSquareForm3,sideDistance(end)];
        sideDistance_squareForm = sideDistance_squareForm - min(sideDistance_squareForm);
        
        cd(dir_tools_homemade)
        sideDistance_squareForm = standardSideHitTemplate();
        

        % with accurate valleys
%         ySquareForm1 = [sideForce(1),squares(1),squares(1),sideForce(iValley(1))];
%         ySquareForm2 = [sideForce(iValley(1)),squares(2),squares(2),sideForce(iValley(2))];
%         ySquareForm3 = [sideForce(iValley(2)),squares(3),squares(3),sideForce(end)];
%         sideForce_squareForm = [ySquareForm1,ySquareForm2,ySquareForm3,sideForce(end)]

        % with valleys of zero
        ySquareForm1 = [0,squareForce(1),squareForce(1),0];
        ySquareForm2 = [0,squareForce(2),squareForce(2),0];
        ySquareForm3 = [0,squareForce(3),squareForce(3),0];
        sideForce_squareForm = [ySquareForm1,ySquareForm2,ySquareForm3,0];
       
         
        
% Prepare the cell by cell data for initial plotting        
        numelDuplicateColumns = round(dimcellForward/12,0);
        sideForce_cell = [];
        for segment = 2:11
            for dup = 1:numelDuplicateColumns
                sideForce_cell(end+1) = sideForce_squareForm(segment);
            end
        end
        
        while numel(sideForce_cell) <= (dimcellForward-1)
            sideForce_cell(end+1) = sideForce_squareForm(end);
        end
        sideDistance_cell = linspace(min(sideDistance_squareForm),max(sideDistance_squareForm),dimcellForward);
        %sideForce_cell_percent = sideForce_cell./max(sideForce_cell);
        sideForce_cell_percent = sideForce_cell./sum(unique(sideForce_cell));
        % make the percentages add up to 1.0, rather than leaving the
        % highest at 100%
        % divide each peak by the total of the three peaks
        % 1 2 3, 1/5, 2/5, 3/5 CB CB CB DR
        % peaks./sum(peaks);
        
        
        %sideForce_list = unique(sideForce_cell);
        %sideForce_list = sideForce_list(2:4);
        %sideForce_list = squareForce;
        
        
        %prepare side vector to become the same dimension as dimcell, via spline interpolation
        forwardDistance_xi=linspace(min(forwardDistanceRange),max(forwardDistanceRange),dimcellForward); 
        forwardForce_xi=linspace(min(forwardForceRange),max(forwardForceRange),dimcellForward); 
        
        forwardDistance_xi=linspace(min(forwardDistanceRange),max(forwardDistanceRange),dimcellForward-2); % attempt to add same distance to ends 
        forwardForce_xi=linspace(min(forwardForceRange),max(forwardForceRange),dimcellForward-2); % attempt to add 0 force to ends 
        
        cd(dir_code)
        [forwardDistanceRange_unique, forwardForceRange_unique] = deleteDuplicates(forwardDistanceRange, forwardForceRange);
        forwardForceRange_interp=interp1(forwardDistanceRange_unique,forwardForceRange_unique,forwardDistance_xi,'spline');
        forwardDistanceRange_interp=forwardDistance_xi;
        
        % attempt to add same distance to ends, to cap the ends
        forwardDistanceRange_interp(end+1)=forwardDistanceRange_interp(end);
        forwardDistanceRange_interp=[forwardDistanceRange_interp(1),forwardDistanceRange_interp];
        
        % attempt to add 0 force to ends 
        if rangestart == min(rangestart_list_keep)
            frontcap = -10;
            endcap = 0;
        elseif rangeend == max(rangeend_list_keep) % this list changes size, 
            frontcap = 0;
            endcap = -10;
        else
            frontcap = 0;
            endcap = 0;
            
        end

        forwardForceRange_interp=[frontcap,forwardForceRange_interp];
        forwardForceRange_interp(end+1)=endcap;
        
        if not(numel(forwardForceRange_interp)==numel(sideForce_cell_percent))
            msg = 'error'
        end
        mat3D_cell=forwardForceRange_interp'.*sideForce_cell_percent;
        [X_cell,Y_cell]=meshgrid([sideDistance_cell],[forwardDistanceRange_interp]);

        % SWITCH ME --> NaN vs 0
%       mat3D_cell(mat3D_cell<.000001)=NaN; % uncomment this to hide 0 ground values
        mat3D_cell(logical([mat3D_cell<.000001].*[mat3D_cell>-1]))=0; % uncomment this to hide 0 ground values
        mat3D_cell(mat3D_cell<0)=0; % uncomment this to hide 0 ground values
        
        % this fixes diagonal warpage from one side of the plot to another,
        % and adds a curtain at x=0, at the cost of a slight incline.
        curtaincolumn_NaN = NaN.*ones(length(mat3D_cell(:,1)),1);
        curtaincolumn_zeros = zeros(length(mat3D_cell(:,end)),1);
        mat3D_cell(:,1) = curtaincolumn_zeros;
        mat3D_cell(:,end) = curtaincolumn_NaN;
        
        % seal the gate, remove floor blanket

        %mat3D_cell = mat3D_cell_copy;
        for n_row = 2:(length(mat3D_cell)-1)
        reprow = mat3D_cell(n_row,:);
        dir_tools_homemade = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Code - Matlab, Python, etc\Code - Matlab - Data Compilation\Utilities\';
        cd(dir_tools_homemade);
        iL1=1;
        iR1=findiR(reprow,iL1);
        iL2=findiL(reprow,iR1);
        iR2=findiR(reprow,iL2);
        iL3=findiL(reprow,iR2);
        iR3=findiR(reprow,iL3);
        
        reprow(reprow==0)=NaN;
        reprow([iL1,iR1,iL2,iR2,iL3,iR3])=0;
        reprow_zeros = reprow;
        reprow_zeros([iL3:iR3])=0;
        reprow([iR1+1:iL2-1,iR2+1:iL3-1])=NaN; % new test CB
        mat3D_cell(n_row,:) = reprow;
        mat3D_cell(1,[iR1+1:iL2-1,iR2+1:iL3-1,iR3+1:end]) = NaN; % clean up extra zeros in the null space
        mat3D_cell(end,[iR1+1:iL2-1,iR2+1:iL3-1,iR3+1:end]) = NaN; % clean up extra zeros in the null space
        
        
        end
        
        %square up the sides.
        %X_cell(:,[iL1,iR1,iL2,iR2,iL3,iR3]) = X_cell(:,[iL1+1,iR1-1,iL2+1,iR2-1,iL3+1,iR3-1]);
        
        % create floor panels
        mat3D_cell_floor = mat3D_cell; 
        [r,c]=size(mat3D_cell_floor);
        for col=1:c
            for row=1:r
                if not(isnan(mat3D_cell_floor(row,col)))
                    % mat3D_cell_floor(row,col) = 0; % build the floor
                    mat3D_cell_floor(row,col) = NaN; % kill the floor
                %else
                    %mat3D_cell_floor(row,col) = NaN;
                end
            end
        end
        
        % make combination matrix, for both surface and floor panels
        mat_nan_combo = NaN.*ones(length(X_cell),length(X_cell));
        X_cell_combo = [[X_cell,X_cell];[mat_nan_combo,mat_nan_combo]];
        Y_cell_combo = [[Y_cell,Y_cell];[mat_nan_combo,mat_nan_combo]];
        mat3D_cell_combo = [[mat3D_cell,mat3D_cell_floor];[mat_nan_combo,mat_nan_combo]];
        
        
        
%         s = mesh(X_cell,Y_cell,mat3D_cell); %%%% turn on
%         hold on
%         mesh(X_cell,Y_cell,mat3D_cell_floor); %%%% turn on

        s = mesh(X_cell_combo,Y_cell_combo,mat3D_cell_combo); hold on %%%% turn on
        
        
        if overwritestuff == 'y'
        S.("3D Matrix (inch*pounds)"){j}=mat3D_cell;
        S.("Force, square waveform (pounds)"){j} = sideForce_cell;
        S.("Distance, square waveform (inches)"){j} = sideDistance_cell;
        end
    end
    


% add to append


    X_append = [X_append,X_cell];
    Y_append = [Y_append,Y_cell];
    mat3D_append = [mat3D_append,mat3D_cell];
    mat3D_append_floor = [mat3D_append_floor,mat3D_cell_floor];
    X_append_combo = [X_append_combo,X_cell_combo];
    Y_append_combo = [Y_append_combo,Y_cell_combo];
    mat3D_append_combo = [mat3D_append_combo,mat3D_cell_combo];
    end
    
end % plot completed, all cells compiled

% fill remainder with nan
[sx,sy]=size(X_append);
if sx<sy
    mat_nan = NaN.*ones(sy-sx,sy);
    X_append = [X_append;mat_nan];
    Y_append = [Y_append;mat_nan];
    mat3D_append = [mat3D_append;mat_nan];
    mat3D_append_floor = [mat3D_append_floor;mat_nan];

else
    msg = 'broken';
end

    [sxc,syc]=size(X_append_combo);
    mat_nan_combo = NaN.*ones(syc-sxc,syc);
    X_append_combo = [X_append_combo;mat_nan_combo];
    Y_append_combo = [Y_append_combo;mat_nan_combo];
    mat3D_append_combo = [mat3D_append_combo;mat_nan_combo];

    
    
    % command to rebuilt and visualize
    %mesh(T.("3D Matrix, X"){i},T.("3D Matrix, Y"){i},T.("3D Matrix, Z"){i})
    %axis equal
    
    % or 
    hold off
    %s = mesh(X_append,Y_append,mat3D_append); hold on; mesh(X_append,Y_append,mat3D_append_floor); axis equal
    s = mesh(X_append_combo,Y_append_combo,mat3D_append_combo); axis equal

    
    axis equal
    zlim([0 4.5])
    titletext = (T.("Plot")(i));
    title(T.("Plot")(i))
    zlabel('Force (pounds)')
    ylabel('Forward Distance (in)')
    xlabel('Side Distance (in)')
    v = [1 -2 0.5];
    %v = [-1 0 0]; % side view
    [caz,cel] = view(v);
    filename_description = '_peaksUsed_noFloor';
    filename_fig = strcat(titletext,filename_description,'.fig');
    filename_png = strcat(titletext,filename_description,'.png');
    sizestr = string(dimcellSide);
    filename_stl = strcat(titletext,'_',sizestr,'x',sizestr,filename_description,'.stl');
    dir_CAD = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\CAD Drawings - Clayton\FieldMap\';
    filename_stl_long = strcat(dir_CAD,filename_stl);
    
    complete3DSurface.XX=X_append; complete3DSurface.YY=Y_append; complete3DSurface.ZZ=mat3D_append;
    
    % make it appear!! 
    % or : mesh(XData{3},YData{3},ZData{3}); axis equal % CB CB CB
    % or : mesh(X_cell,Y_cell,mat3D_cell); axis equal
    
    % plot whole surface for entire plot
    % or : mesh(X_append,Y_append,mat3D_append); axis equal;
    % or : mesh(T.("3D Matrix, X"){i},T.("3D Matrix, Y"){i},T.("3D Matrix, Z"){i}); axis equal;
    % or : mesh(complete3DSurface.XX,complete3DSurface.YY,complete3DSurface.ZZ); axis equal;
    
    % does not include endcaps:
    % or : mesh(T.("3D Matrix, X"){i},T.("3D Matrix, Y"){i},T.("3D Matrix, Z"){i}); axis equal;
    
    % does include endcaps
    % or : mesh(T.("3D Matrix Cells")(i).XX,T.("3D Matrix Cells")(i).YY,T.("3D Matrix Cells")(i).ZZ); axis equal;
    
    

    cd(dir_tools_downloaded)
    %T.("3D Matrix, X"){i} = X_append;
    %T.("3D Matrix, Y"){i} = Y_append;
    %T.("3D Matrix, Z"){i} = mat3D_append;
    %T.("3D Matrix Cells")(i)=complete3DSurface; %CB % does include endcaps
    if overwritestuff == 'y'
    T.("3D Matrix, X"){i} = X_append;
    T.("3D Matrix, Y"){i} = Y_append;
    T.("3D Matrix, Z"){i} = mat3D_append;
    T.("3D Matrix Cells")(i)=complete3DSurface; %CB % does include endcaps
    dir_images = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Images, Figures, Graphs, Plots, Charts\Wheat 2021\Images - SOCEM\3D Imaging\';
    cd(dir_images)
    saveas(s,filename_png)
    saveas(s,filename_fig)
    cd(dir_tools_downloaded)
    surf2stl(char(filename_stl_long),X_append_combo, Y_append_combo, mat3D_append_combo);
    %vrml(gcf,filename_wrl)
    end
    dir_images = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Images, Figures, Graphs, Plots, Charts\Wheat 2021\Images - SOCEM\3D Imaging\';
    cd(dir_images)
    %saveas(s,filename_png)
    %saveas(s,filename_fig)
    cd(dir_tools_downloaded)
    % surf2stl(char(filename_stl_long),X_append_combo, Y_append_combo, mat3D_append_combo);
    %vrml(gcf,filename_wrl)
    xlim;
    ylim;
    cd(dir_code);
end

%% Add Bottom and sides, and bridge gaps, in 3D plots, to create a watertight surface/object
for i=1:height(T)
X = T.("3D Matrix Cells")(i).XX;
Y = T.("3D Matrix Cells")(i).YY;
mat3D = T.("3D Matrix Cells")(i).ZZ;
n=length(X);

leftrightcurtain_row = zeros(1,n);
leftrightcurtain_column = zeros(n,1);
%X_curtain = [leftrightcurtain_column;X_append;leftrightcurtain_column];
% 
% How to find only tangentional zeros?
% X axis, going up, look for value change.
% Find index of solo zero before not zero. Row 1 left. i1L
% Find index of first zero after not zero. Row 1 right. i1R
% Find index of last zero before not zero. Row 2 left. i2L
% Find index of first zero after not zero. Row 2 right. i2R
% Find index of last zero before not zero. Row 3 left. i3L
% Find index of first zero after not zero. Row 3 right. i3R
% %for each cell
% convert to NaN all values between in mat3D for each row for indices:(iR1:i2L),(iR2:i3L), (i3R:end) 
% create copy of mat3D. For all not(isnan()) values, change to 0. This will create  bottom surface.

%%   sand 
mat3D_cell = mat3D_cell_copy;
reprow = mat3D_cell(2,:);
%dir_tools = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Code - Matlab, Python, etc\Code - Matlab - Data Compilation\Utilities\';
%cd(dir_tools);
iL1=1;
iR1=findiR(reprow,iL1);
iL2=findiL(reprow,iR1);
iR2=findiR(reprow,iL2);
iL3=findiL(reprow,iR2);
iR3=findiR(reprow,iL3);
reprow(reprow==0)=NaN;
reprow([iL1,iR1,iL2,iR2,iL3,iR3])=0;
reprow_zeros = reprow;
reprow_zeros([iL3:iR3])=0;

for n_row = 2:(length(mat3D_cell)-1)
mat3D_cell(n_row,:) = reprow;
end








end

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Here there be sunken ships
%% EI plotting, S vs T
X=[];
Y=[];
for i=1:height(T)
j_list = find(T.Plot(i)==S.Plot);
i_list = ones(numel(j_list),1).*i;
x=S.("EI-M (lbs*in^2)")(j_list);
y=T.("EI-M (lbs*in^2)");%(i_list);
%y=T.("Instron EI (lbs*in^2)");%(i_list);
X(end+1) = mean(x);
Y(end+1) = mean(y);
X=x;
Y=y;
%hold on
%plot(X,Y,'o','Color',colormat(i,:))
end


hold on
[mbc,m,b,c,Rsq,RMSE,SSE,lm,f0,string2021] = linearFitting(X,Y,1,1,1,'Color','k');

legend('Soft Winter Wheat, 13 plots','Best Fit','Location','northeast')
str2021 = {'f(x) = m*x + b'; string2021{2}; extractBefore(string2021{3},20);'-';'August 13 forward-hit data';'used custom bar-heights.';'-';'August 23 side-hit data';'used a constant non-discerning';'bar-height setting of 5.75 in.'};
ha21=annotation(gcf,'textbox',[0.55,0.13,1,1],'String',str2021,'EdgeColor','none','FitBoxToText','on','verticalalignment', 'bottom', 'color','k');

xlabel('EI-M (lbs*in^2), SOCEM Side Hits, August 23^r^d')
ylabel('EI-M (lbs*in^2), SOCEM Forward Hits, August 13^t^h')
%ylabel('EI (lbs*in^2), Instron Average')
title('Forward Hits versus Side Hits, SOCEM 2021')
%title('Instron Average versus Side Hits, SOCEM 2021')
%title('SOCEM Forward Hits versus Instron Average, 2021')

%% create averaged Instron table
plots=unique(Instron.Plot);
for i=1:numel(plots)
    plotEI_Nmmsqr=mean(Instron.EI(Instron.Plot==plots(i)));
    plotEI_lbinsqr=plotEI_Nmmsqr.*Newtons2Pounds.*mmsqr2insqr;
    Socem.("Instron EI (lbs*in^2)")(find(Socem.Plot==plots(i)))=plotEI_lbinsqr;
end
%% Replace raw data in S with raw data from T
for i=1:height(S)
S.("Force/row (lbs)")(i) = T.("Force/row (lbs)")(i);
S.("Distance (in)")(i) = T.("Distance (in)")(i);
S.("Time (s)")(i) = T.("Time (s)")(i);
end
%% gander
x=linspace(1,100,numel(forwardForceRange));
plot(x,forwardForceRange)
y=linspace(1,100,numel(sideForce));
plot(y,sideForce)

%% See Raw, per T(i,:)
for i=1:height(T)
%i=4;
forwardDistance = cell2mat(T.("Distance (in)")(i));
forwardForce = cell2mat(T.("Force/row (lbs)")(i));
j_list = find(T.Plot(i)==S.Plot);
try
    close(f2)
end
f2=figure(2);
for k = 1:numel(j_list)
    j=j_list(k);
    sideForce = cell2mat(S.("Force/row (lbs)")(j));
    sideDistance = cell2mat(S.("Distance (in)")(j));
    
    mat3D_cell = S.("3D Matrix (inch*pounds)"){j};
    sideForce_cell = S.("Force, square waveform (pounds)"){j};
    sideDistance_cell = S.("Distance, square waveform (inches)"){j};
    localstem=T.("Stem heights at x (in.)"){k};
    localhorz=T.("Horizontal point of vertical height measurement (in.)"){k};
    rangestart = S.("Range Start (in)")(j);
    rangeend = S.("Range End (in)")(j);
    localhorz<rangestart
    
    
    subplot(numel(j_list),1,k)
    plot(sideDistance-min(sideDistance),sideForce)
    hold on
    plot(sideDistance_cell,sideForce_cell)
    %plot(S.("Distance, square waveform (inches)"){j},S.("Force, square waveform (pounds)"){j})
    xstring = strcat(string(S.("Range Start (in)")(j))," in to ",string(S.("Range End (in)")(j)), " in");
    xlabel(xstring)
    legendstring = strcat("Avg Stem Height = ",string(round(S.("Avg height (in)")(j),2)));
    %a2=annotation(legendstring,'location','northwest');
    %a2{k}=annotation(gcf,'textbox',[0.55,0.13,1,1],'String',legendstring,'EdgeColor','none','FitBoxToText','on','verticalalignment', 'bottom', 'color','k');
    %text(.15*max(sideDistance),0.9*max(sideForce),legendstring)
end
    titlestring = {strcat(T.Plot(i),', Side Hits, Aug 23'); strcat("Bar Height = 5.75, Avg Stem Height = ",string(round(T.("Avg height (in)")(i),2)))};
    title(f2.Children(end), titlestring);
    %if k == round(numel(j_list)/2,0)
        %ylabel(f2.Children(round(end/2,0)),'Force (pounds)')
    %end
    ylabel('Force (pounds)')
f2.Position = [404.0000   89.5000  299.0000  720.5000];
dir_images = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Images, Figures, Graphs, Plots, Charts\Wheat 2021\Images - SOCEM\3D Imaging\';
cd(dir_images)
filename = strcat(titlestring{1},'_peaks.png');
saveas(f2,filename)
cd(dir_code)
end
%% See all Raw
for j=1:height(S)
    hold off
    close gcf
    sideForce = cell2mat(S.("Force/row (lbs)")(j));
    sideDistance = cell2mat(S.("Distance (in)")(j));
    sideTime = cell2mat(S.("Time (s)")(j));
    plot(sideDistance,sideForce)
    hold on 
    plot(S.("Distance, square waveform (inches)"){j},S.("Force, square waveform (pounds)"){j})
    
    pause(0.2)
end
%% generate SW plots
hold off
for i=1:height(T)
    plot(T.("Distance (in)"){i},T.("Force/row (lbs)"){i}.*T.("Rows")(i))
    titlestring = strcat(T.("Plot")(i), ', August 13');
    title(titlestring )
    xlabel('Distance (in)')
    ylabel('Force (pounds)')
    dir_images = 'D:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Images, Figures, Graphs, Plots, Charts\Wheat 2021\Images - SOCEM\Raw, Standard Experiment\';
    cd(dir_images)
    filename = strcat(titlestring,'.png');
    saveas(gcf,filename)

end
cd(dir_code)

%% binning for homogeneity
for i=1:height(T)
hold off
close gcf
richlevel=T.("3D Matrix, Z"){i}; % incorrect
richlevel_reshape = reshape(richlevel,numel(richlevel),1);
richlevel_reshape = richlevel_reshape(~isnan(richlevel_reshape));
stddev = std(richlevel_reshape);
homogeneity = stddev/(max(richlevel_reshape)-min(richlevel_reshape))*100; %
sizerichlevel = size(richlevel);
numelbins = 20;
bins = linspace(min(richlevel_reshape),max(richlevel_reshape),numelbins+1);
populations = zeros(numelbins+1,1);
for j=1:numelbins
populations(j) = sum(sum(logical([bins(j)<richlevel].*[richlevel<bins(j+1)])));
end
bins = bins(1:end-1);
populations = populations(1:end-1).*100;
bar(bins,populations/numel(richlevel_reshape*100));
dir_images = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Images, Figures, Graphs, Plots, Charts\Wheat 2021\Images - SOCEM\3D Imaging\';
cd(dir_images)
xlabel(' Force Bin (pounds)')
ylabel('% of Plot in Bin')
stringAnnotateHomo = {strcat('Standard deviation = ',string(homogeneity),' %')};
ha3=annotation(gcf,'textbox',[0.55,0.83,1,1],'String',stringAnnotateHomo,'EdgeColor','none','FitBoxToText','on','verticalalignment', 'bottom', 'color','k');
title(strcat(T.Plot(i),' Homogeneity'));
pause(0.5)
filename = strcat(T.Plot(i),'_homogenityAnalysisV2.png');
saveas(gcf,filename)
end
cd(dir_code)
%% transformation matrices