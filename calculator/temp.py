from astropy.table import Table, vstack
from os import listdir
import astropy.units as u
import numpy as np

read_dir = './atmosphere/original_plaintext_files/'
write_dir = './atmosphere/files/'

# for filename in listdir(read_dir):
#     t = Table.read(read_dir + filename, format='ascii.ecsv')
#     t['wav'].unit = u.angstrom
#     t['eff'].unit = u.electron / u.photon
#     t.meta = { key.upper(): val for key, val in t.meta.items() }
#     for key, val in t.meta.items():
#         if val == 'None':
#             t.meta[key] = 'none'
#     for column in t.keys():
#         t[column.upper()] = t[column]
#         del t[column]
#     t.write(read_dir + filename, format='ascii.ecsv', overwrite=True)

for filename in listdir(read_dir):
    t = Table.read(read_dir + filename, format='ascii.ecsv')
    t.meta['AIRMASS'] = t.meta['airmass']
    t.meta['VAPOR'] = t.meta['water_vapor']
    del t.meta['airmass']
    del t.meta['water_vapor']
    print(write_dir + filename.split('.')[0] + '.fits')
    t.write(write_dir + filename.split('.')[0] + '.fits', format='fits', overwrite=True)


# wav = np.arange(310, 900, 0.02) * u.nm

# # CHECK W/ SHERRY ABOUT EMISSIONS
# add = Table.read('atmosphere/optical.txt', format='ascii.ecsv')
# em = np.interp(wav, add['wavelength'], add['flux'])

# TRANSMISSION
# orig = [310,320,340,360,380,400,450,500,550,600,650,700,800,900] * u.nm
# tra = [1.37,0.82,0.51,0.37,0.30,0.25,0.17,0.13,0.12,0.11,0.11,0.10,0.07,0.05] * u.Unit('')
# tra = np.interp(wav, orig, tra)
# #print([u.Magnitude(x.value).physical for x in tra] * u.Unit(''))


# for filename in listdir('atmosphere/original_plaintext_files'):
#     if filename.startswith('mk_skybg'):
#         t = Table.read('atmosphere/original_plaintext_files/' + filename, format='ascii.ecsv')
#         new = Table({'wavelength': wav, 'flux': em})
#         t = vstack([new, t])
#         t['wavelength'] = [round(x, 3) for x in t['wavelength']]
#         t['wavelength'].unit = u.nm
#         t.write('atmosphere/original_plaintext_files/' + filename, format='ascii.ecsv', overwrite=True)
