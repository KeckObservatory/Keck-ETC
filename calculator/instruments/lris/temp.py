from astropy.table import Table, vstack
from os import listdir
import astropy.units as u
from astropy.io import fits
import numpy as np

write_dir = './throughput/'
read_dir = './plaintext_files/'

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

# for filename in listdir(read_dir):
#     if filename.endswith('.fits'):
#         o = fits.open(read_dir + filename, format='fits')
#         t = Table({'WAV': o[2].data['WAV'][0], 'EFF': o[2].data['EFF'][0]})
#         t['WAV'].unit = u.angstrom
#         t.meta['DICHROIC'] = 'D' + str(o[1].data['BLOCKING'][0])
#         if o[1].data['INSTRUMENT'] == 'LRISBLUE':
#             t.meta['GRISM'] = str(o[1].data['GRATING'][0])
#             savename = 'b_' + t.meta['DICHROIC'] + '_' + t.meta['GRISM'].replace('/','-') + '.txt'
#         else:
#             t.meta['GRATING'] = str(o[1].data['GRATING'][0])
#             savename = 'r_' + t.meta['DICHROIC'] + '_' + t.meta['GRATING'].replace('/','-') + '.txt'
        
#         print(write_dir + savename)
#         t.write(write_dir + savename, format='ascii.ecsv', overwrite=True)


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

####################################################


# # dichroic data
# def ref(dichroic):
#     x = dichroic['WAV'] * u.angstrom
#     return lambda w: np.interp(w, x, (1 - dichroic['TRANS']/0.95) * 0.98)

# def tra(dichroic):
#     x = dichroic['WAV'] * u.angstrom
#     return lambda w: np.interp(w, x, dichroic['TRANS'])

# d460 = Table.read('unmodified_files/dichroic_460_t.dat', format='ascii')
# d500 = Table.read('unmodified_files/dichroic_500_t.dat', format='ascii')
# d560 = Table.read('unmodified_files/dichroic_560_t.dat', format='ascii')
# d680 = Table.read('unmodified_files/dichroic_680_t.dat', format='ascii')
# blue = {
#     'MIRROR': lambda w: 1.0, 'D460': ref(d460), 'D500': ref(d500), 'D560': ref(d560), 'D680': ref(d680), 'CLEAR': lambda w: 0.0
# }
# red = {
#     'MIRROR': lambda w: 0.0, 'D460': tra(d460), 'D500': tra(d500), 'D560': tra(d560), 'D680': tra(d680), 'CLEAR': lambda w: 1.0
# }

for dichroic in ['MIRROR', 'D460', 'D500', 'D560', 'D680', 'CLEAR']:
    for file in listdir(read_dir):
        if file.startswith('blue') and dichroic in file:
            blue = Table.read(read_dir + file, format='ascii.ecsv')
            
            for file in listdir(read_dir):
                if file.startswith('red') and dichroic in file:
                    red = Table.read(read_dir + file, format='ascii.ecsv')

                    x = np.linspace(blue['WAV'][0], red['WAV'][-1], 2000)

                    new = Table({
                        'WAV': x,
                        'EFF': np.interp(x, blue['WAV'], blue['EFF'], left=0, right=0) + np.interp(x, red['WAV'], red['EFF'], left=0, right=0)
                    })
                    new['WAV'].unit = u.angstrom
                    new.meta['DICHROIC'] = dichroic
                    new.meta['GRISM'] = blue.meta['GRISM']
                    new.meta['GRATING'] = red.meta['GRATING']
                    new.meta['FILTER'] = 'none'
                    new.meta['MODE'] = 'spectroscopic'
                    print(new.meta['DICHROIC'] + '_' + new.meta['GRATING'].replace('/','-') + '_' + new.meta['GRISM'].replace('/','-') + '.fits')
                    new.write(write_dir + new.meta['DICHROIC'] + '_' + new.meta['GRATING'].replace('/','-') + '_' + new.meta['GRISM'].replace('/','-') + '.fits', format='fits', overwrite=True)

