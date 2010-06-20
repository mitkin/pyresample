#pyresample, Resampling of remote sensing image data in python
# 
#Copyright (C) 2010  Esben S. Nielsen
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Resample image from one projection to another 
using nearest neighbour method in cartesian projection coordinate systems"""

import numpy as np

import geometry
import _spatial_mp


def get_image_from_linesample(row_indices, col_indices, source_image,
                              fill_value=0):
    """Samples from image based on index arrays.

    :Parameters:
    row_indices : numpy array 
        Row indices. Dimensions must match col_indices
    col_indices : numpy array 
        Col indices. Dimensions must match row_indices
    source_image : numpy array 
        Source image
    fill_value : {int, None} optional 
            Set undetermined pixels to this value.
            If fill_value is None a masked array is returned 
            with undetermined pixels masked
    
    :Returns: 
    image_data : numpy array
        Resampled image 
    """
    
    #mask out non valid row and col indices
    row_mask = (row_indices >= 0) * (row_indices < source_image.shape[0])
    col_mask = (col_indices >= 0) * (col_indices < source_image.shape[1])
    valid_rows = row_indices * row_mask
    valid_cols = col_indices * col_mask

    #free memory
    del(row_indices)
    del(col_indices)

    #get valid part of image
    target_image = source_image[valid_rows, valid_cols]
    
    #free memory
    del(valid_rows)
    del(valid_cols)

    #create mask for valid data points
    valid_data = row_mask * col_mask
    if valid_data.ndim != target_image.ndim:
        for i in range(target_image.ndim - valid_data.ndim):
            valid_data = np.expand_dims(valid_data, axis=valid_data.ndim)
            
    #free memory
    del(row_mask)
    del(col_mask)
    #fill the non valid part of the image
    if fill_value is not None:
        target_filled = (target_image * valid_data + 
                         (1 - valid_data) * fill_value)
    else:
        if np.ma.is_masked(target_image):
            mask = ((1 - valid_data) | target_image.mask)
        else:
            mask = (1 - valid_data)
        target_filled = np.ma.array(target_image, mask=mask)
    
    return target_filled.astype(target_image.dtype)
    
def get_linesample(lons, lats, source_area_def, nprocs=1):
    """Returns index row and col arrays for resampling
    
    :Parameters:
    lons : numpy array 
        Lons. Dimensions must match lats
    lats : numpy array   
        Lats. Dimensions must match lons
    source_area_def : object 
        Source definition as AreaDefinition object
    nprocs : int, optional 
        Number of processor cores to be used
    
    :Returns:
    (row_indices, col_indices) : tuple of numpy arrays
        Arrays for resampling area by array indexing
    """
    
     #Proj.4 definition of source area projection
    if nprocs > 1:
        source_proj = _spatial_mp.Proj_MP(**source_area_def.proj_dict)
    else:
        source_proj = _spatial_mp.Proj(**source_area_def.proj_dict)

    #get cartesian projection values from longitude and latitude 
    source_x, source_y = source_proj(lons, lats, nprocs=nprocs)

    #Find corresponding pixels (element by element conversion of ndarrays)
    source_pixel_x = (source_area_def.pixel_offset_x + \
                      source_x / source_area_def.pixel_size_x).astype(np.int)
    
    source_pixel_y = (source_area_def.pixel_offset_y - \
                      source_y / source_area_def.pixel_size_y).astype(np.int)
                    
    return source_pixel_y, source_pixel_x
                          
def get_image_from_lonlats(lons, lats, source_area_def, source_image_data, 
                           fill_value=0, nprocs=1):
    """Samples from image based on lon lat arrays 
    using nearest neighbour method in cartesian projection coordinate systems.

    :Parameters:
    lons : numpy array 
        Lons. Dimensions must match lats
    lats : numpy array   
        Lats. Dimensions must match lons
    source_area_def : object 
        Source definition as AreaDefinition object
    source_image_data : numpy array 
        Source image data
    fill_value : {int, None} optional 
            Set undetermined pixels to this value.
            If fill_value is None a masked array is returned 
            with undetermined pixels masked    
    nprocs : int, optional 
        Number of processor cores to be used
    
    :Returns:
    image_data : numpy array 
        Resampled image data
    """

    source_pixel_y, source_pixel_x = get_linesample(lons, lats, 
                                                    source_area_def, 
                                                    nprocs=nprocs)

    #Return target image
    return get_image_from_linesample(source_pixel_y, source_pixel_x,
                                     source_image_data, fill_value)

def get_resampled_image(target_area_def, source_area_def, source_image_data,
                        fill_value=0, nprocs=1):
    """Resamples image using nearest neighbour method in cartesian 
    projection coordinate systems.

    :Parameters:
    target_area_def : object 
        Target definition as AreaDefinition object
    source_area_def : object 
        Source definition as AreaDefinition object
    source_image_data : numpy array 
        Source image data
    fill_value : {int, None} optional 
            Set undetermined pixels to this value.
            If fill_value is None a masked array is returned 
            with undetermined pixels masked    
    nprocs : int, optional 
        Number of processor cores to be used
    
    :Returns:
    image_data : numpy array 
        Resampled image data    
    """
    
    if not isinstance(target_area_def, geometry.AreaDefinition):
        raise TypeError('target_area_def must be of type AreaDefinition')
    if not isinstance(source_area_def, geometry.AreaDefinition):
        raise TypeError('source_area_def must be of type AreaDefinition')
    if not isinstance(source_image_data, (np.ndarray,
                                          np.ma.core.MaskedArray)):
        raise TypeError('source_image must be of type ndarray'
                        ' or a masked array.')

    #Get lon lat arrays of target area
    lons, lats = target_area_def.get_lonlats(nprocs)
    
    #Get target image
    return get_image_from_lonlats(lons, lats, source_area_def, 
                                  source_image_data, fill_value, nprocs)




        