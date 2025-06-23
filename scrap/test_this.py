import matplotlib.pyplot as plt

import cartopy.crs as ccrs


def plot_city_lights():
    # Define resource for the NASA night-time illumination data.
    base_uri = 'https://map1c.vis.earthdata.nasa.gov/wmts-geo/wmts.cgi'
    layer_name = 'VIIRS_CityLights_2012'

    # Create a Cartopy crs for plain and rotated lat-lon projections.
    plain_crs = ccrs.PlateCarree()
    rotated_crs = ccrs.RotatedPole(pole_longitude=120.0, pole_latitude=45.0)

    fig = plt.figure()

    # Plot WMTS data in a specific region, over a plain lat-lon map.
    ax = fig.add_subplot(1, 2, 1, projection=plain_crs)
    ax.set_extent([-6, 3, 48, 58], crs=ccrs.PlateCarree())
    ax.coastlines(resolution='50m', color='yellow')
    ax.gridlines(color='lightgrey', linestyle='-')
    # Add WMTS imaging.
    ax.add_wmts(base_uri, layer_name=layer_name)

    # Plot WMTS data on a rotated map, over the same nominal region.
    ax = fig.add_subplot(1, 2, 2, projection=rotated_crs)
    ax.set_extent([-6, 3, 48, 58], crs=ccrs.PlateCarree())
    ax.coastlines(resolution='50m', color='yellow')
    ax.gridlines(color='lightgrey', linestyle='-')
    # Add WMTS imaging.
    ax.add_wmts(base_uri, layer_name=layer_name)

    plt.show()


if __name__ == '__main__':
    plot_city_lights()