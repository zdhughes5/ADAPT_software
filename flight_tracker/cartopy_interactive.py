import matplotlib.pyplot as plt

import cartopy.crs as ccrs


def main():
    url = 'https://map1c.vis.earthdata.nasa.gov/wmts-geo/wmts.cgi'
    layer = 'VIIRS_CityLights_2012'

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.add_wmts(url, layer)
    ax.set_extent([-15, 25, 35, 60], crs=ccrs.PlateCarree())

    ax.set_title('Suomi NPP Earth at night April/October 2012')
    plt.show()


if __name__ == '__main__':
    main()