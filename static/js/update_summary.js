// Input -- source = {data: {'column':[1,2,3,4,...], ...}, ...}
//          input = {location: wavelength in nm, ...}
//          exp = {text: text to replace, ...}
//          wav = {text: text to replace, ...}
//          snr = {text: text to replace, ...}
//          flux = {text: text to replace, ...}
//          time = {text: text to replace, ...}

// Find closest index in data to the given wavelength
const wavelength = input.location;
const closest = source.data['wavelengths'].reduce(function(prev, curr) {
    return (Math.abs(curr - wavelength) < Math.abs(prev - wavelength) ? curr : prev);
});
const index = source.data['wavelengths'].indexOf(closest);

// Set exp. text
const exp_val = source.data.exposure[index];
exp.text = exp_val < 9999 ? String(exp_val.toFixed(0))+' s' : String(exp_val.toExponential(1))+' s';

// Set snr text
const snr_val = source.data.snr[index];
snr.text = snr_val < 9999 ? String(snr_val.toFixed(2)) : String(snr_val.toExponential(2));

// Set wavelength text
wav.text = String((source.data.wavelengths[index]/1000).toFixed(3))+' \u03BCm';

// Set flux text
flux.text = String(source.data.flux[index].toExponential(0))+' flam';

// Set integration time text
const time_val = source.data.integration[index];
time.text = time_val < 9999 ? String(time_val.toFixed(0))+' s' : String(time_val.toExponential(1))+' s';