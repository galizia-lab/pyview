function [granules_labeled, summary_stats] = CalciSeg(stack, varargin)
% [granules_labeled, summary_stats] = CalciSeg(stack, Name, Value)
% segments the spatial aspects of a 3-D stack (x*y*time) into individual
% regions ('granules') based on a refined 2D Delaunay triangulation.
% Note: CalciSeg uses parallel for-loops at for the local growing
% algorithm and the refinement process. It is recommended to start a
% parallel pool of workers before calling the function.
%
%
% OPTIONAL INPUT PARAMETERS:
% Parameter name        Values and description
% =========================================================================
%
% 'projection_method' : Method for calculating the projection
% (string)              across time.
%                       Default: 'std'
%                       - 'std'    : Standard deviation projection
%                       - 'mean'   : Mean intensity projection
%                       - 'median' : Median intensity projection
%                       - 'max'    : Maximum intensity projection
%                       - 'min'    : Minimum intensity projection
%                       - 'pca'    : Principal component projection. For
%                                    this, "stack" is projected into PC 
%                                    space.
%                       - 'corr'   : Correlation space as local correlation
%                                    between  neighboring pixels
%                       - 'none'   : Applicable when "stack" has no third 
%                                    dimension or when to take the first 
%                                    slice of the 3-D stack
%
% 'init_seg_method'   : Method for the initial segmentation.
% (string)              Default: 'voronoi'
%                       - 'voronoi' : Delaunay triangulation
%                       - 'corr'    : Local growing based on correlation.
%                                     This will set 'projection_method' to
%                                     be 'corr'
%                       - 'rICA'    : Reconstruction independent component 
%                                     analysis.
%
% 'regmax_method'     : Method for determining how to identify local
% (string)              extrema in the intensity projection.
%                       Default: 'raw'
%                       - 'raw'      : Simply apply imregionalmax/-min on
%                                      the projection. 
%                       - 'filtered' : Dilate/erode image to apply moving
%                                      max/min filter before applying
%                                      imregionalmax/-min. Note, this
%                                      will also smooth the correlation 
%                                      space when init_seg_method is set to
%                                      be 'corr', or the independent
%                                      components accordingly when it is 
%                                      set to be 'rICA'.
%                       - 'both'     : Combine both above-mentioned
%                                      methods. Note, this is only
%                                      applicable when init_seg_method is
%                                      set to be 'voronoi'. 
%
% 'n_rep'             : Number of iterations for refining the regions.
% (integer)             Default: 0
%
% 'refinement_method' : Measure to fine-tune granule assignment during 
% (string)              refinement iterations.
%                       Default: 'rmse'
%                       - 'rmse' : Root median square error
%                       - 'corr' : Pearson  correlation coefficient
%                       
% 'limitPixCount'     : Limits the pixel area per granule
% (matrix or string)    Default:  [1 inf]
%                       - [a, b] : The minimum (a) and maximum (b) number
%                                  of pixels that can be assigned to a
%                                  granule. Note that, the minimum size
%                                  affects the filter size for the 
%                                  regmax_method input.
%                       - 'auto' : An automatic assessment based on the 
%                                  distribution of granule sizes before
%                                  refinement. Here, a is set to be the
%                                  5th quantile and b to be the 95th
%                                  quantile. The filter size for    
%                                  regmax_method is set to 1.
%
% 'corr_thresh'       : Threshold for the Pearson correlation coefficient
% (number)              when refinement_method is set to be 'corr'.
%                       Default: 0.85
%
% 'n_rICA'            : Number of features to extract during reconstruction 
% (integer)             independent component analysis.
%                       Default: 0 to use the full number of components.
%                       Otherwise provide a number larger than zero for
%                       either an undercomplete (n_rICA < number of frames)
%                       or overcomplete (n_rICA > number of frames) feature 
%                       representations.
%
% 'n_PCA'             : Percentage of the total variance of the data that
% (number)              should be kept if the projection_method is set to
%                       'pca'. The value must be larger than zero and not
%                       exceed 100.
%                       Default: 100
%
% 'fillmissing'       : Replace NaNs or Infs by linear interpolation of 
% (logical)             neighboring, nonmissing values.
%                       Default: false
%
% 'resume_CalciSeg'    : Map with granule IDs from a previous segmentation
% (2-D matrix)          session. Providing this input will skip all initial
%                       segmentation step and directly jump to refinement.
%                       Default: []
%
% 'pool_fragments'    : Sometimes, granules belonging to the same bio-
% (logical)             logical structure are fragmented into one or
%                       multiple pieces. To account for this, we 
%                       calculate the Pearson correlation coefficient 
%                       between neighboring granules and pool them if the 
%                       correlation exceeds the threshold set using input 
%                       'corr_thresh' (default: 0.85). The neighbor 
%                       comparison is repeated until no granule pair 
%                       exceeds the threshold. Note that this setting  
%                       ignores the upper limit for pixel area per granule 
%                       since it is applied after the refinement step.
%                       Default: false
%
%
% OUTPUT
% Parameter name      Values and description
% =========================================================================
%
% granules_labeled    : Map with granule IDs. The size of granules_labeled
%                       corresponds to the first two dimensions of stack.
%
% summary_stats       : Summary statistics for each granule and additional
%                       inforamtion on the segmentation process saved as
%                       structures.
%                      - projection           : Projection image used for
%                                               initial segmentation.
%                      - avgTCs               : Each granule's mean time 
%                                               course
%                      - granule_Corr         : Average within-granule 
%                                               correlation
%                      - granule_Avg_img      : Within-granule average 
%                                               activity
%                      - granule_Std_img      : Each granule's standard  
%                                               deviation over time
%                      - granule_Max_img      : Each granule's maximum 
%                                               value over time
%                      - granule_Min_img      : Each granule's minimum
%                                               value over time
%                      - granule_Corr_img     : Within-granule correlation
%                      - active_region.map    : Binary map of active 
%                                               regions based on Otsu's
%                                               method
%                      - active_region.method : Method used for binarizing
%
%
% Version: 11-Oct-24 (R2023a)
% =========================================================================

% Check whether this is the lates version
checkVersion(...
    fileread([mfilename('fullpath'),'.m']),...
    webread('https://raw.githubusercontent.com/yannickguenzel/CalciSeg/main/code/CalciSeg.m'))

% Validate inputs
stack = squeeze(stack);
opt = validateInputs(stack, varargin);

% Reduce precision of stack to be single
stack_size = whos('stack');
if ~strcmp(stack_size.class, 'single')
    stack = single(stack);
end%if not single precision

% Check for missing data
if any(isnan(stack(:))) || any(isinf(stack(:)))
    if opt.fillmissing
        % Fill missnig data
        stack(isinf(stack)) = NaN;
        stack = fillmissing(stack, "linear");
    else
        error('The stack contains NaN or inf values. Please check your data or set the input "fillmissing" to true.')
    end%if fill
end%if missing data

% Define size for local neighborhood
if isnumeric(opt.limitPixCount)
    opt.filter_size = ceil(sqrt(opt.limitPixCount(1)/pi)) + double(opt.limitPixCount(1)==0);
    % Make sure it is an odd number
    opt.filter_size = opt.filter_size + double((mod(opt.filter_size,2)==0));
elseif strcmp(opt.limitPixCount, 'auto')
    opt.filter_size = 1;
end

% Initial preprocessing
[stack, reshaped_stack, projection] = initialPreprocessing(stack, opt);

% Perform initial segmentation
granules_labeled = initialSegmentation(stack, reshaped_stack, projection, opt);

% Maybe, the user wants to have the min/max size estimated based on the data
if (isstring(opt.limitPixCount) || ischar(opt.limitPixCount)) && strcmp(opt.limitPixCount, 'auto')
    % Get pixel count for each region
    granuleList = unique(granules_labeled);
    [~,~,C] = unique(granules_labeled);
    C = histcounts(C, 1:length(granuleList)+1);
    C = [C(:), granuleList(:)];
    opt.limitPixCount = [floor(quantile(C(2:end,1), 0.05)), floor(quantile(C(2:end,1), 0.95))];
    disp(['automatic assessment of the min./max. granule size: [', num2str(opt.limitPixCount),']'])
end%if auto min size

% Refine segmentation
% Account for regions that are too small or too large. For this,
% check each region that has less or more than the required number
% of pixels. Note, first run removeHugeRegions, as this may create tiny
% regions.
granules_labeled = removeHugeRegions(granules_labeled, opt.limitPixCount(2));
granules_labeled = removeTinyRegions(reshaped_stack, granules_labeled, opt);
if opt.n_rep>0
    granules_labeled = refineSegmentation(reshaped_stack, granules_labeled, opt);
end%if refine

% Check for fragmented granules
if opt.pool_fragments
    granules_labeled = poolFagmentedGranules(reshaped_stack, granules_labeled, opt);
end%if pool fragments

% Ensure that the highest ID equals the number of granules 
granules_labeled = finalRefinement(granules_labeled);

% Final refinement steps and statistics calculation
if nargout>1
    [granules_labeled, summary_stats] = regionStats(reshaped_stack, granules_labeled, opt);
    summary_stats.projection = projection;
end%if summary stats

end%FCN:CalciSeg

% -------------------------------------------------------------------------

function checkVersion(localVersion, GitHubVersion)
if ~strcmp(localVersion, GitHubVersion)
    % Display a warning message
    msg = sprintf(['The local version of the CalciSeg does not match the latest version on GitHub. \n', ...
        'Please update your script to ensure you are using the most recent version. \n', ...
        'Latest version can be found at: https://github.com/YannickGuenzel/CalciSeg']);
    warning('CalciSeg:version',msg);
end
end%FCN:checkVersion

function opt = validateInputs(stack, varargin)
% First, set all parameters to their default value
opt.projection_method = 'std';
opt.init_seg_method = 'voronoi';
opt.regmax_method = 'raw';
opt.n_rep = 0;
opt.refinement_method = 'rmse';
opt.limitPixCount = [1 inf];
opt.corr_thresh = 0.85;
opt.n_rICA = 0;
opt.n_PCA = 100;
opt.fillmissing = false;
opt.resume_CalciSeg = [];
opt.pool_fragments = false;

% Now, check optional input variable
varargin = varargin{1};
if ~isempty(varargin)
    if mod(length(varargin),2)>0
        error('Wrong number of arguments.')
    else
        % Iterate over all inuput arguments
        for iArg = 1:2:length(varargin)
            switch varargin{iArg}
                % Projection method -------------------------------------------
                case 'projection_method'
                    valid_projection_methods = {'std', 'mean', 'median', 'max', 'min', 'pca', 'corr', 'none'};
                    if ~ismember(varargin{iArg+1}, valid_projection_methods)
                        error('Invalid "projection_method". Valid options are: %s.', strjoin(valid_projection_methods, ', '));
                    else
                        opt.projection_method = varargin{iArg+1};
                    end
                    % Initial segmentation method ---------------------------------
                case 'init_seg_method'
                    valid_init_seg_methods = {'voronoi', 'corr', 'rICA'};
                    if ~ismember(varargin{iArg+1}, valid_init_seg_methods)
                        error(sprintf('Invalid "init_seg_method". Valid options are: %s.', strjoin(valid_init_seg_methods, ', ')));
                    else
                        opt.init_seg_method = varargin{iArg+1};
                    end
                    % Method for smoothing regional maxima ------------------------
                case 'regmax_method'
                    valid_regmax_methods = {'raw', 'filtered', 'both'};
                    if ~ismember(varargin{iArg+1}, valid_regmax_methods)
                        error('Invalid "regmax_method". Valid options are: %s.', strjoin(valid_regmax_methods, ', '));
                    else
                        opt.regmax_method = varargin{iArg+1};
                    end
                    % Number of refinement interations ----------------------------
                case 'n_rep'
                    if ~isnumeric(varargin{iArg+1}) || varargin{iArg+1} < 0
                        error('Input "n_rep" must be a non-negative integer value.');
                    else
                        opt.n_rep = varargin{iArg+1};
                    end
                    % Distance metric during refinement ---------------------------
                case 'refinement_method'
                    valid_refinement_methods = {'corr', 'rmse'};
                    if ~ismember(varargin{iArg+1}, valid_refinement_methods)
                        error('Invalid "refinement_method". Valid options are: %s.', strjoin(valid_refinement_methods, ', '));
                    else
                        opt.refinement_method = varargin{iArg+1};
                    end
                    % Minimum and maximum number of pixels per region -------------
                case 'limitPixCount'
                    if ~isnumeric(varargin{iArg+1}) && ~strcmp(varargin{iArg+1}, 'auto')
                        error( 'Input "limitPixCount" must be a non-negative pair of two integer values or "auto".');
                    elseif isnumeric(varargin{iArg+1}) && length(varargin{iArg+1}) ~= 2
                        error('Input "limitPixCount" must be a non-negative pair of two integer values or "auto".');
                    else
                        opt.limitPixCount = varargin{iArg+1};
                    end
                    % Correlation threshold ---------------------------------------
                case 'corr_thresh'
                    if ~isnumeric(varargin{iArg+1}) || varargin{iArg+1} < 0 || varargin{iArg+1} > 1
                        error('Input "corr_thresh" must be a number between 0 and 1.');
                    else
                        opt.corr_thresh = varargin{iArg+1};
                    end
                    % Number of independent components ----------------------------
                case 'n_rICA'
                    if ~isnumeric(varargin{iArg+1}) || varargin{iArg+1} < 0
                        error('Input "n_rICA" must be an integer larger than 0.');
                    else
                        opt.n_rICA = round(varargin{iArg+1});
                    end
                case 'n_PCA'
                    if ~isnumeric(varargin{iArg+1}) || varargin{iArg+1} <= 0 || varargin{iArg+1} > 100
                        error('Input "n_PCA" must be an number larger than 0 and smaller than 100.');
                    else
                        opt.n_PCA = round(varargin{iArg+1});
                    end
                case 'fillmissing'
                    if ~islogical(varargin{iArg+1})
                        error('Input "fillmissing" must be a logical true or false.');
                    else
                        opt.fillmissing = varargin{iArg+1};
                    end
                case 'resume_CalciSeg'
                    if ~isnumeric(varargin{iArg+1}) || length(size(varargin{iArg+1})) > 2 || size(varargin{iArg+1},1) ~= size(stack,1) || size(varargin{iArg+1},2) ~= size(stack,2)
                        error('Input "resume_CalciSeg" must be a 2-D matrix of integers with the same spatial size as "stack".');
                    else
                        opt.resume_CalciSeg = single(varargin{iArg+1});
                    end
                case 'pool_fragments'
                    if ~islogical(varargin{iArg+1})
                        error('Input "pool_fragments" must be a logical true or false.');
                    else
                        opt.pool_fragments = varargin{iArg+1};
                    end
                otherwise
                    error(['Unknown argument "',varargin{iArg},'"'])
            end%switch
        end%iArg
    end%if mod
end%if custom arguments

% Last, validate 'stack' input and potentially adjust some input parameters
if ndims(stack) < 2
    error('Input "stack" has to be at least a 2-D (x,y) matrix.')
elseif ndims(stack) > 3
    error('Number of dimension of the input "stack" cannot exceed 4.')
elseif ismatrix(stack)
    warning('Input "stack" has no temporal component. Inputs are adjusted accordingly (projection_method="none"; init_segment_method="voronoi"; refinement_method="rmse").');
    opt.projection_method = 'none';
    opt.init_seg_method = 'voronoi';
    opt.refinement_method = 'rmse';
end%if invalid 'stack' input
% For the region-growing approach, both projection_method and
% opt.init_seg_method must be set to 'corr'
if strcmp(opt.init_seg_method, 'corr')
    if ~strcmp(opt.projection_method, 'corr')
        warning('When the input "init_seg_method" is set to "corr", the input "projection_method" must be set to "corr" as well. We fixed this.')
        opt.projection_method = 'corr';
    end%if
end%if
end%FCN:validateInputs

% -------------------------------------------------------------------------

function [stack, reshaped_stack, projection] = initialPreprocessing(stack, opt)

% Get the size of the stack
[x, y, t] = size(stack);

% Initialize the projection variable
projection = [];

% Calculate the projection based on the specified method
switch opt.projection_method
    case 'std'
        projection = nanstd(stack, [], 3);
    case 'mean'
        projection = nanmean(stack, 3);
    case 'median'
        projection = nanmedian(stack, 3);
    case 'max'
        projection = nanmax(stack, [], 3);
    case 'min'
        projection = nanmin(stack, [], 3);
    case 'pca'
        [~, stack, ~, ~, explained] = pca(reshape(stack, [x*y, t]));
        if ~isempty(find(cumsum(explained)>=opt.n_PCA,1))
            t = find(cumsum(explained)>=opt.n_PCA,1);
        end%if
        stack = reshape(stack(:,1:t), [x, y, t]);
        projection = squeeze(stack(:,:,1));
        disp(['PC1 | Explained variance: ', num2str(round(explained(1),2)), '%'])       
    case 'corr'
        projection = correlationImage(stack, opt);
    case 'none'
        projection = squeeze(stack(:,:,1));
end%switch projection method

% Reshape the stack to a 2D matrix for further processing
reshaped_stack = reshape(stack, [x*y, t]);

end%FCN:initialPreprocessing

% -------------------------------------------------------------------------

function granules_labeled = initialSegmentation(stack, reshaped_stack, projection, opt)
switch opt.init_seg_method
    case 'voronoi'
        % Get local maxima and minima
        [regional_maxima, regional_minima] = identifyLocalExtrema(projection, opt);
        % 2-D Delaunay triangulation
        granules_labeled = triang_extrema(regional_maxima, regional_minima);
    case 'corr'
        granules_labeled = growing_regions(stack, projection, reshaped_stack, opt);
    case 'rICA'
        granules_labeled = rICA_segmentation(projection, reshaped_stack, opt);
        % Check for splits
        granules_labeled = checkSplits(granules_labeled);
end%switch opt.init_seg_method
end%FCN:initialSegmentation

% -------------------------------------------------------------------------

function granules_labeled = triang_extrema(regional_maxima, regional_minima)
% Erode the extrema location to keep the centroids only
ultimateErosion = bwulterode(regional_maxima>0) + bwulterode(regional_minima>0);
% Include points that are on the edge of the image. Later, we will set all
% regions that are at the edge to zero
ultimateErosion(1,:) = 1; ultimateErosion(:,1) = 1;
ultimateErosion(end,:) = 1; ultimateErosion(:,end) = 1;
% Segment image based on these maxima using a 2-D Delaunay
% triangulation
% Get linear indices of local maxima
linearIndices = find(ultimateErosion);
% Convert linear indices to (x, y, z) coordinates
[Cx, Cy] = ind2sub(size(ultimateErosion), linearIndices);
% Combine coordinates into Nx3 matrix
C = [Cx, Cy]; clear Cx Cy
% Segment image based on these maxima using a 2-D Delaunay
% triangulation (i.e. assign pixels to the closest extreme point
% Convert linear indices to (x, y) coordinates
linearIndices = 1:numel(regional_maxima);
[x, y] = ind2sub(size(regional_maxima), linearIndices);
% Combine all and adjust aspect ratio;
allVoxels = [x(:), y(:)];
clear x y z linearIndices
% Use knnsearch to find the index of the closest point in 'C' for each voxel
granules_labeled = knnsearch(C, allVoxels);
% Reshape the resulting index array to the dimensions of the 3D volume
granules_labeled = reshape(granules_labeled, size(regional_maxima));
% Remove border
ultimateErosion(1,:) = 0; ultimateErosion(:,1) = 0;
ultimateErosion(end,:) = 0; ultimateErosion(:,end) = 0;
linearIndices = find(ultimateErosion);
% Create a logical mask
mask = ismember(granules_labeled, granules_labeled(linearIndices));
granules_labeled(~mask) = 0;
end%FCN:triang_extrema

% -------------------------------------------------------------------------

function [regional_maxima, regional_minima] = identifyLocalExtrema(projection, opt)
% Initialize the output variables
regional_maxima = [];
regional_minima = [];
SE = strel('disk', opt.filter_size);
% Identify the local extrema based on the specified method
switch opt.regmax_method
    case 'raw'
        regional_maxima = imregionalmax(projection, 8);
        regional_minima = imregionalmin(projection, 8);
    case 'filtered'
        projection_max_filtered = imdilate(projection, SE);
        projection_min_filtered = imerode(projection, SE);
        regional_maxima = imregionalmax(projection_max_filtered, 8);
        regional_minima = imregionalmin(projection_min_filtered, 8);
    case 'both'
        projection_max_filtered = imdilate(projection, SE);
        projection_min_filtered = imerode(projection, SE);
        regional_maxima = imregionalmax(projection, 8) | imregionalmax(projection_max_filtered, 8);
        regional_minima = imregionalmin(projection, 8) | imregionalmin(projection_min_filtered, 8);
end%switch opt.regmax_method
end%FCN:identifyLocalExtrema

% -------------------------------------------------------------------------

function projection = correlationImage(stack, opt)
% Get a map of local correlatios of a pixel with each of its neighbors
% --- Preallocation
projection = zeros(size(stack,1), size(stack,2));
corr_img = projection;
% --- Get number of pixels
px_cnt = numel(corr_img);
% --- Get a mask to identify neighbors
nMask = strel('disk', opt.filter_size);
nMask = nMask.Neighborhood;
elementIndex = size(nMask,1); elementIndex = (elementIndex / 2) + 0.5;
nMask(elementIndex, elementIndex) = 0;
% Iterate over all pixel
parfor iPx = 1:px_cnt
    % Create mask  including all neighbors
    neighbors = zeros(size(projection));
    neighbors(iPx) = 1;
    neighbors = conv2(neighbors, nMask, 'same')==1;
    neighbors(iPx) = 0;
    % Get neighbors' indices
    [neighbors_ind_X, neighbors_ind_Y] = ind2sub(size(neighbors), find(neighbors));
    [px_ind_X, px_ind_Y] = ind2sub(size(neighbors), iPx);
    % Get the correlation
    neighbors_TC = squeeze(mean(mean(stack(neighbors_ind_X, neighbors_ind_Y,:))));
    corr_img(iPx) = corr(neighbors_TC, squeeze(stack(px_ind_X, px_ind_Y, :)));
end%iPx
projection = corr_img;
end%FCN:correlationImage

% -------------------------------------------------------------------------

function granules_labeled = growing_regions(stack, corr_img, reshaped_stack, opt)
% Check whether there is an upper limit to the region size
if isnumeric(opt.limitPixCount)
    max_size = opt.limitPixCount(2);
else
    max_size = 1;
end
% Now, start with the best local correlation and gradually increase the
% region until we reach a threshold of a correlation that got too bad
% --- Preallocation
granules_labeled = zeros(size(corr_img));
% --- Counter for regions
cnt_id = 1;
% Iterate over all pixels
px_cnt = numel(corr_img);
hWait = waitbar(0, ['Growing regions ... ', num2str(0),'/',num2str(px_cnt)]);
for iPx = 1:px_cnt
    waitbar(iPx/px_cnt, hWait, ['Growing regions ... ', num2str(iPx),'/',num2str(px_cnt)])
    % Get the current correlation value
    [~, max_id] = max(corr_img(:));
    if corr_img(max_id) >= opt.corr_thresh
        % This will be the origin of a new region
        granules_labeled(max_id) = cnt_id;
        while true
            % Get the current region's TC
            curr_TC = mean(reshaped_stack(find(granules_labeled==cnt_id),:),1);
            % Get the neighbors
            neighbors = imdilate(granules_labeled == cnt_id, strel('disk', 1)) - (granules_labeled == cnt_id);
            [neighbors_ind_X, neighbors_ind_Y] = ind2sub(size(neighbors), find(neighbors));
            % Keep track of whether pixels got added
            added_px = zeros(1, length(neighbors_ind_X));
            % Check neighbors
            if (length(neighbors_ind_X) + sum(granules_labeled(:)==cnt_id)) > max_size
                stop_ind = (length(neighbors_ind_X) + sum(granules_labeled(:)==cnt_id)) - max_size;
            else
                stop_ind = 0;
            end
            for iN = 1:length(neighbors_ind_X(1:end-stop_ind))
                if (granules_labeled(neighbors_ind_X(iN), neighbors_ind_Y(iN)) == 0) && (corr(curr_TC(:), squeeze(stack(neighbors_ind_X(iN), neighbors_ind_Y(iN),:))) >= opt.corr_thresh)
                    granules_labeled(neighbors_ind_X(iN), neighbors_ind_Y(iN)) = cnt_id;
                    added_px(iN) = 1;
                end%if valid addition
            end%iN
            % Check break criterion
            if sum(added_px) == 0 || sum(granules_labeled(:)==cnt_id) >= max_size
                break
            end% if no more
        end%while
        % Dont check the current pixels anymore
        corr_img(granules_labeled == cnt_id) = -inf;
        cnt_id = cnt_id+1;
    end%if good enough
end%iPx
close(hWait)
end%FCN:growing_regions

% -------------------------------------------------------------------------

function granules_labeled = rICA_segmentation(projection, reshaped_stack, opt)
% Employ a reconstruction independent component analysis (rICA) to extract
% features that can be turned into individual regions. For this, determine
% the component with the strongest effec on a given pixel.
% Get size of the dataset
[x, y] = size(projection);
% Subtract mean since ICA cannot separate sources with a mean signal
% effect.
reshaped_stack = reshaped_stack-nanmean(reshaped_stack,1);
% Prewhiten the signal so that so that it has zero mean and identity 
% covariance.
reshaped_stack = prewhiten(reshaped_stack);
% Apply PCA
[~,reshaped_stack] = pca(reshaped_stack);
% Check how many components to request
if opt.n_rICA==0
    opt.n_rICA = size(reshaped_stack, 2);
end
% Apply reconstruction ICA (rICA)
rng(1)% For reproducibility
ricaTransform = rica(reshaped_stack, opt.n_rICA, 'VerbosityLevel', 1);
% Transform the data using the fitted model
transformedData = transform(ricaTransform, reshaped_stack);
% Correct sign
TD = transformedData;
TDv = TD ./ repmat(std(TD), size(TD,1), 1);
TDzp = TDv - 2;
TDzp(TDzp < 0) = 0;
TDzpm = mean(TDzp);
TDzn = TDv + 2;
TDzn(TDzn > 0) = 0;
TDznm = mean(TDzn);
transformedData = TD .* repmat(sign(TDzpm + TDznm), size(TD, 1), 1);
% Reshape the independent components back into a 3-D format
reshaped_stack = reshape(transformedData, [x, y, size(transformedData,2)]);
% Smooth components
if strcmp(opt.regmax_method, 'filtered')
    reshaped_stack = imboxfilt3(reshaped_stack, [opt.filter_size, opt.filter_size, 1]);
end%if filter
% Get the component with the strongest effect on a given pixel
[~, granules_labeled] = max(reshaped_stack, [], 3);
end%FCN:rICA_segmentation

% -------------------------------------------------------------------------

function Z = prewhiten(X)
    % From https://de.mathworks.com/help/stats/extract-mixed-signals.html
    % 1. Size of X.
    [N,P] = size(X);
    assert(N >= P);
    % 2. SVD of covariance of X. We could also use svd(X) to proceed but N
    % can be large and so we sacrifice some accuracy for speed.
    [U,Sig] = svd(cov(X));
    Sig     = diag(Sig);
    Sig     = Sig(:)';
    % 3. Figure out which values of Sig are non-zero.
    tol = eps(class(X));
    idx = (Sig > max(Sig)*tol);
    assert(~all(idx == 0));
    % 4. Get the non-zero elements of Sig and corresponding columns of U.
    Sig = Sig(idx);
    U   = U(:,idx);
    % 5. Compute prewhitened data.
    mu = mean(X,1);
    Z = X-mu;
    Z = (Z*U)./sqrt(Sig);
end%FCN:prewhiten

% -------------------------------------------------------------------------

function granules_labeled = refineSegmentation(reshaped_stack, granules_labeled, opt)
% Get mask for neighbors
nMask = [0 1 0; 1 0 1; 0 1 0];
% Refine granules
previous_granules_labeled = -ones(size(granules_labeled));
hWait = waitbar(0, ['Refine regions ... 0/',num2str(opt.n_rep)]);
for iRep = 1:opt.n_rep
    waitbar(iRep/opt.n_rep, hWait, ['Refine regions ... ', num2str(iRep),'/',num2str(opt.n_rep)])
    % Get avg signal trace per granule
    granuleList = unique(granules_labeled);
    granuleTC = nan(length(granuleList), size(reshaped_stack,2));
    for iGranule = 1:length(granuleList)
        idx = find(granules_labeled==granuleList(iGranule));
        granuleTC(iGranule, :) = nanmean(reshaped_stack(idx,:),1);
    end%iGranule
    clear iC iR iGranule
    % Get pixels in border regions. But only take regions into account
    % that changed
    ind = find(granules_labeled~=previous_granules_labeled);
    keep_changed_IDs = unique([granules_labeled(ind(:)); previous_granules_labeled(ind(:))]);
    mask = ismember(granules_labeled, keep_changed_IDs);
    candidates = imgradient(granules_labeled, "intermediate")>0;
    candidates(~mask) = 0;
    idx_candidates = find(candidates);
    idx_table = reshape(1:numel(granules_labeled), size(granules_labeled));
    % Iterate over all pixels in border regions and check
    % whether they have to be re-assigned.
    previous_granules_labeled = granules_labeled;
    switch opt.refinement_method
        case 'corr'
            idx_candidates_newIdentiy = refinement_parfor_corr(idx_candidates, idx_table, granules_labeled, reshaped_stack, granuleTC, granuleList, nMask);
        case 'rmse'
            idx_candidates_newIdentiy = refinement_parfor_rmse(idx_candidates, idx_table, granules_labeled, reshaped_stack, granuleTC, granuleList, nMask);
    end
    % Update changed identities
    granules_labeled(idx_candidates) = idx_candidates_newIdentiy;
    % Account for splitting of granules. For this, iterate over
    % all granulee and check whether the corresponding itentity
    % can be found in more than one coherent region
    granules_labeled = checkSplits(granules_labeled);
    % Account for regions that are too small or too large. For this,
    % check each region that has less or more than the required number
    % of pixels. Note, first run removeHugeRegions, as this may create tiny
    % regions.
    granules_labeled = removeHugeRegions(granules_labeled, opt.limitPixCount(2));
    granules_labeled = removeTinyRegions(reshaped_stack, granules_labeled, opt);
    % Stop if no changes
    if sum(previous_granules_labeled(:) == granules_labeled(:)) == numel(granules_labeled(:))
        break
    end% if change
end%iRep
close(hWait)
% Make sure the highest ID is equal to the number of granules
[~, ~, newIDs] = unique(granules_labeled);
granules_labeled = reshape(newIDs, size(granules_labeled));
end%FCN:refineSegmentation

% -------------------------------------------------------------------------

function idx_candidates_newIdentiy = refinement_parfor_corr(idx_candidates, idx_table, granules_labeled, reshaped_stack, granuleTC, granuleList, nMask)
% Get current labels and prepare output of new labels
idx_candidates_Identiy = granules_labeled(idx_candidates);
idx_candidates_newIdentiy = idx_candidates_Identiy;
% Use a parallel for loop to speed things up
parfor iCan = 1:length(idx_candidates)
    % Get indices of neighbors
    idx_neighbor = conv2( double(idx_table==idx_candidates(iCan)), nMask, 'same')==1;
    % Get neighborhood clusters
    nC = unique(granules_labeled(idx_neighbor));
    % Get the pixel's TC
    activity_px = reshaped_stack(idx_candidates(iCan), :);
    % Check which neighborhood is a better fit
    voronoi_R = zeros(length(nC),1);
    for iN = 1:length(nC)
        activity_cluster = granuleTC(granuleList == nC(iN), :);
        r = corrcoef(activity_px, activity_cluster); voronoi_R(iN) = abs(diff([1, r(2)]));
    end%iN
    % Assign new identity
    [~, iBest] = min(voronoi_R);
    idx_candidates_newIdentiy(iCan) = nC(iBest);
end%iCan
end%FCN:refinement_parfor_corr

% -------------------------------------------------------------------------

function idx_candidates_newIdentiy = refinement_parfor_rmse(idx_candidates, idx_table, granules_labeled, reshaped_stack, granuleTC, granuleList, nMask)
% Get current labels and prepare output of new labels
idx_candidates_Identiy = granules_labeled(idx_candidates);
idx_candidates_newIdentiy = idx_candidates_Identiy;
% Use a parallel for loop to speed things up
parfor iCan = 1:length(idx_candidates)
    % Get indices of neighbors
    idx_neighbor = conv2( double(idx_table==idx_candidates(iCan)), nMask, 'same')==1;
    % Get neighborhood clusters
    nC = unique(granules_labeled(idx_neighbor));
    % Get the pixel's TC
    activity_px = reshaped_stack(idx_candidates(iCan), :);
    % Check which neighborhood is a better fit
    voronoi_R = zeros(length(nC),1);
    for iN = 1:length(nC)
        activity_cluster = granuleTC(granuleList == nC(iN), :);
        voronoi_R(iN) = sqrt(median((activity_cluster-activity_px).^2));
    end%iN
    % Assign new identity
    [~, iBest] = min(voronoi_R);
    idx_candidates_newIdentiy(iCan) = nC(iBest);
end%iCan
end%Fcn:refinement_parfor_rmse

% -------------------------------------------------------------------------

function granules_labeled = checkSplits(granules_labeled)
% Account for splitting of granules. For this, iterate over
% all granule and check whether the corresponding itentity
% can be found in more then one coherent regions
% Identifying Splitter Candidates
unique_granules = unique(granules_labeled);
splitter_candidates = [];
parfor iP = 1:length(unique_granules)
    % Get region mask
    region_id = unique_granules(iP);
    region_mask = (granules_labeled == region_id);
    % Label connected components within the region
    [~, num] = bwlabel(region_mask, 4);
    % If more than one connected component, then it's a splitter
    if num > 1
        splitter_candidates = [splitter_candidates, region_id];
    end%if splitter
end%iP
% Iterate over all splitters and account for them
for iGranule = 1:length(splitter_candidates)
    % Get b/w image and identify number of regions
    bw = granules_labeled==splitter_candidates(iGranule);
    L = bwlabel(bw,4);
    % If there is more than one region (i.e. more than
    % the labels 0 and 1, assign new identities
    unique_L = unique(L(:));
    if length(unique_L)>2
        % Iterate over all splitter
        for iSplitter = 3:length(unique_L)
            idx = find(L == unique_L(iSplitter));
            % If the new region is just a single pixel, do not make it
            % a new region
            if length(idx)==1
                % Get pixels on the edge
                neighbors = imgradient(L == unique_L(iSplitter), 'central')>0;
                neighbors(bw) = 0;
                neighbor_IDs = unique(granules_labeled(neighbors));
                granules_labeled(idx) = mode(neighbor_IDs(:));
            else
                granules_labeled(idx) = max(unique_granules)+1;
                unique_granules = [unique_granules(:); max(unique_granules)+1];
            end
        end%iSplitter
    end% if more
end%iGranule
end%FCN:checkSplits

% -------------------------------------------------------------------------

function granules_labeled = removeTinyRegions(reshaped_stack, granules_labeled, opt)
% Kick out granules that are too small. For this, iterate
% over all granules, and check whether it is large enough. If
% not, assign it to the best neighbour.
% Repeat as long as all small granules are gone.
small_granules = inf;
while ~isempty(small_granules)
    % Get pixel count for each region
    granuleList = unique(granules_labeled);
    [~,~,C] = unique(granules_labeled);
    C = histcounts(C, 1:length(granuleList)+1);
    C = [C(:), granuleList(:)];
    % Sort base don count
    C = sortrows(C,1,"ascend");
    % Iterate over all regions and take care of those that are too small.
    % Note: only take the first and then check again. Otherwise we may get
    % stuck by combining all pixels!
    small_granules = C(C(:, 1) < opt.limitPixCount(1), 2);
    % Get the ID of the current granule
    curr_ID = C(1,2);
    % Get a logical image for the current granule
    bw = granules_labeled==curr_ID;
    % Get the pixels of the current granule
    ind_pix = find(bw);
    % Get the current time course
    curr_TC = nanmean(reshaped_stack(ind_pix, :), 1);
    % Get pixels on the edge
    neighbors = imgradient(bw, 'central')>0;
    neighbors(bw) = 0;
    neighbor_IDs = unique(granules_labeled(neighbors));
    % Get the neighbors' time courses
    TCs = nan(length(neighbor_IDs), size(reshaped_stack,2));
    for iTC = 1:length(neighbor_IDs)
        ind = find(granules_labeled==neighbor_IDs(iTC));
        TCs(iTC,:) = nanmean(reshaped_stack(ind,:),1);
    end%iTC    
    % Check which neighboring granule is the best fit
    id_table = nan(1, length(neighbor_IDs));
    for iN = 1:length(neighbor_IDs)
        % Get the rmse or distance based on correlation
        switch opt.refinement_method
            case 'corr'
                min_dist = corrcoef(curr_TC, TCs(iN,:)); min_dist = abs(diff([1, min_dist(2)]));
            case 'rmse'
                min_dist = sqrt(median(curr_TC - TCs(iN,:)).^2);
        end
        id_table(iN) = min_dist;
    end%iN
    % Assign all pixels of the current granule to the best fitting neighbor
    [~,best_id] = min(id_table);
    granules_labeled(ind_pix) = neighbor_IDs(best_id(1));
end%while
end%FCN:removeTinyRegions

% -------------------------------------------------------------------------

function granules_labeled = removeHugeRegions(granules_labeled, maxPixCount)
% Kick out granules that are too large. For this, iterate
% over all granules, and check whether it is small enough. If
% not, split the region by watershedding it
% Repeat as long as all small granules are gone.
large_granules = inf;
while ~isempty(large_granules)
    % Get pixel count for each region
    granuleList = unique(granules_labeled);
    [~,~,C] = unique(granules_labeled);
    C = histcounts(C, 1:length(granuleList)+1);
    C = [C(:), granuleList(:)];
    % Sort base don count
    C = sortrows(C,1,"descend");
    % Iterate over all regions and take care of those that are too large
    large_granules = C(C(:, 1) > maxPixCount, 2);
    for iGranule = 1:length(large_granules)
        % Get the ID of the current granule
        curr_ID = C(iGranule,2);
        % Get a logical image for the current granule
        bw = granules_labeled==curr_ID;
        % Watershed
        D = bw;
        D = bwdist(~D);
        D = -D;
        L = watershed(D);
        L(~bw) = 0;
        bw_cut = L>0;
        bw_cut = bwlabel(bw_cut);
        % Sometimes, this does not work for circular shapes. For
        % this, cut along the minor axis.
        if ~any(bw(bw) ~= bw_cut(bw))
            % Get the minor axis
            stats = regionprops(bw, 'Centroid', 'MajorAxisLength', 'MinorAxisLength', 'Orientation');
            ellipse = stats(1);
            longAxis = ellipse.MajorAxisLength;
            shortAxis = ellipse.MinorAxisLength;
            % Get the position and anle of the ellipse
            centerX = ellipse.Centroid(1);
            centerY = ellipse.Centroid(2);
            angle = ellipse.Orientation;
            % Define the minor axis
            x1 = floor(centerX - (shortAxis/2) * cosd(angle));
            y1 = floor(centerY - (shortAxis/2) * sind(angle));
            x2 = ceil(centerX + (shortAxis/2) * cosd(angle));
            y2 = ceil(centerY + (shortAxis/2) * sind(angle));
            % Draw a line
            numPoints = sqrt(size(bw,1)^2+size(bw,2)^2);
            x = round(linspace(x1, x2, numPoints)); x(x<1)=1; x(x>size(bw_cut,2))=size(bw_cut,2);
            y = round(linspace(y1, y2, numPoints)); y(y<1)=1; y(y>size(bw_cut,1))=size(bw_cut,1);
            for iPx = 1:numPoints
                bw_cut(y(iPx), x(iPx), :) = 0;
            end%iPx
            bw_cut = bwlabel(bw_cut,4);
            % If this still did not work, try cutting along the long
            % axis
            if ~any(bw(bw) ~= bw_cut(bw))
                % Define the minor axis
                x1 = floor(centerX - (longAxis/2) * cosd(angle));
                y1 = floor(centerY - (longAxis/2) * sind(angle));
                x2 = ceil(centerX + (longAxis/2) * cosd(angle));
                y2 = ceil(centerY + (longAxis/2) * sind(angle));
                % Draw a line
                numPoints = sqrt(size(bw,1)^2+size(bw,2)^2);
                x = round(linspace(x1, x2, numPoints)); x(x<1)=1; x(x>size(bw_cut,2))=size(bw_cut,2);
                y = round(linspace(y1, y2, numPoints)); y(y<1)=1; y(y>size(bw_cut,1))=size(bw_cut,1);
                for iPx = 1:numPoints
                    bw_cut(y(iPx), x(iPx), :) = 0;
                end%iPx
                bw_cut = bwlabel(bw_cut,4);
            end%did not work
        end%did not work
        % Account for separating lines.
        bw_fill = bw_cut;
        ind = find(bw_cut==0 & bw==1);
        for iPx = 1:length(ind)
            % Get the current pixel's neighborhood
            neighborhood = zeros(size(bw));
            neighborhood(ind(iPx)) = 1;
            neighbors = imgradient(neighborhood, 'central')>0;
            neighbors(ind(iPx)) = 0;
            neighbor_IDs = unique(bw_cut(neighbors));
            bw_fill(ind(iPx)) = max(neighbor_IDs);
        end%iPx
        bw_cut = bw_fill;
        % Update granules_labeled
        bw_cut(ind) = max(bw_cut(:))+1 : max(bw_cut(:))+length(ind);
        bw_cut = bw_cut+max(granules_labeled(:))+1;
        granules_labeled(bw) = bw_cut(bw);
    end%iGranule
end%while
end%FCN:removeHugeRegions

% -------------------------------------------------------------------------

function granules_labeled = poolFagmentedGranules(reshaped_stack, granules_labeled, opt)
% Do this until all pairs are pooled
while true
    % Get a list of granules
    granuleList = unique(granules_labeled);
    % Get each granule's time course
    avgTCs = nan(length(granuleList), size(reshaped_stack,2));
    for iGranule = 1:length(granuleList)
        % Get their index positions
        idx_granule = find(granules_labeled==granuleList(iGranule));
        % Get the avg time course of the current granule
        avgTCs(iGranule,:) = nanmean(reshaped_stack(idx_granule,:),1);
    end%iGranule
    % Get the pairwise correlation between granules
    corrMat = corr(avgTCs', avgTCs');
    % Kick out upper triangle and diagonal
    corrMat(triu(true(size(corrMat)), 1)) = 0;
    corrMat(1:size(corrMat,1)+1:end) = 0;
    % Check all pairs above a certain level and combine them if they are
    % neighbors
    [corrMat_x, corrMat_y] = find(corrMat > opt.corr_thresh);
    % Iterate over all
    combineIDs = nan(length(corrMat_x), 2);
    for iTC = 1:length(corrMat_x)
        % Check whether the two time courses belong to neighbornig pixels
        region1 = (granules_labeled == granuleList(corrMat_x(iTC)));
        region2 = (granules_labeled == granuleList(corrMat_y(iTC)));
        dilated_region1 = imdilate(region1, strel('square', 3));
        dilated_region2 = imdilate(region2, strel('square', 3));
        are_neighbors = any(dilated_region1(:) & region2(:)) || any(region1(:) & dilated_region2(:));
        if are_neighbors
            combineIDs(iTC,:) = [granuleList(corrMat_x(iTC)), granuleList(corrMat_y(iTC))];
        end%if neighbors
    end%iTC
    combineIDs(any(isnan(combineIDs),2),:) = [];
    % Stop, when there is nothing left to pool
    if isempty(combineIDs)
        break
    end%if empty
    % Get a all connected IDs
    G = graph(combineIDs(:,1), combineIDs(:,2));
    bin = conncomp(G);
    % Check all groups
    for iG = 1:max(bin)
        % Get ID list
        ID_list = find(bin == iG);
        if length(ID_list)>1
            % Assign a new ID to those connected
            newID = max(granules_labeled(:))+1;
            newID = max(ID_list);
            for iID = 1:length(ID_list)
                granules_labeled(granules_labeled==ID_list(iID)) = newID;
            end%iID
        end%if connected
    end%iG
end%while
end%FCN:poolFagmentedGranules

% -------------------------------------------------------------------------

function granules_RElabeled = finalRefinement(granules_labeled)
% Preallocation
granules_RElabeled = zeros(size(granules_labeled));
% Get list of granules
granuleList = unique(granules_labeled);
% Iterate over all granules and relabel them
for iG = 1:length(granuleList)
    % Get location of current region
    ind = find(granules_labeled == granuleList(iG));
    % Relabel with increasing number of IDs
    granules_RElabeled(ind) = iG;
end%iG
end%FCN:finalRefinement

% -------------------------------------------------------------------------

function [granules_labeled, summary_stats] = regionStats(reshaped_stack, granules_labeled, opt)
% Pool pixels belonging to the same granule
% --- Get list of granules
granuleList = unique(granules_labeled);
% --- Preallocation
summary_stats.avgTCs = nan(length(granuleList), size(reshaped_stack,2));
summary_stats.granule_Corr = nan(length(granuleList), 1);
summary_stats.granule_Avg_img = nan(size(granules_labeled));
summary_stats.granule_Min_img = nan(size(granules_labeled));
summary_stats.granule_Max_img = nan(size(granules_labeled));
summary_stats.granule_Std_img = nan(size(granules_labeled));
summary_stats.granule_Max_img = nan(size(granules_labeled));
summary_stats.granule_Corr_img = nan(size(granules_labeled));
% Iterate over all granules
for iGranule = 1:length(granuleList)
    % Get their index positions
    idx_granule = find(granules_labeled==granuleList(iGranule));
    % Get the avg time course of the current granule
    summary_stats.avgTCs(iGranule,:) = nanmean(reshaped_stack(idx_granule,:),1);
    % Get within-granule correlation
    summary_stats.granule_Corr(iGranule,1) = calculateAverageCorrelation(summary_stats.avgTCs(iGranule,:), reshaped_stack(idx_granule,:));
    % Project different metrics like the avg or std into 2D
    % --- mean
    summary_stats.granule_Avg_img(idx_granule) = nanmean(summary_stats.avgTCs(iGranule,:));
    % --- min
    summary_stats.granule_Min_img(idx_granule) = nanmin(summary_stats.avgTCs(iGranule,:));
    % --- max
    summary_stats.granule_Max_img(idx_granule) = nanmax(summary_stats.avgTCs(iGranule,:));
    % --- std
    summary_stats.granule_Std_img(idx_granule) = nanstd(summary_stats.avgTCs(iGranule,:));
    % --- corr
    summary_stats.granule_Corr_img(idx_granule) = summary_stats.granule_Corr(iGranule,1);
end%iGranule
% Based on the projection method, estimate which regions are active
switch opt.projection_method
    case 'std'
        summary_stats.active_region.map = imbinarize(summary_stats.granule_Std_img);
        summary_stats.active_region.method = 'std';
    case 'mean'
        summary_stats.active_region.map = imbinarize(summary_stats.granule_Avg_img);
        summary_stats.active_region.method = 'mean';
    case 'max'
        summary_stats.active_region.map = imbinarize(summary_stats.granule_Max_img);
        summary_stats.active_region.method = 'max';
    case 'none'
        summary_stats.active_region.map = [];
        summary_stats.active_region.method = 'none';
end%switch projection method
end%FCN:regionStats

% -------------------------------------------------------------------------

function overallAvg = calculateAverageCorrelation(avg_tc, ind_tc)
% Calculate the average correlation with the centroid
if size(avg_tc, 2)>1
    % --- Preallocation
    corr_values = nan(1, size(ind_tc,1));
    for iPx = 1:size(ind_tc,1)
        r = corrcoef(ind_tc(iPx,:), avg_tc);
        corr_values(iPx) = r(2);
    end%iPx
    overallAvg = nanmean(corr_values);
else
    overallAvg = NaN;
end%if more dimensions
end%FCN:calculateAverageCorrelation