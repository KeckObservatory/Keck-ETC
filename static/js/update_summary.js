// Input -- source = {data: {'column':[1,2,3,4,...], ...}, ...}
// Input -- cb_obj = {x: wavelength in nm, ...}

const wavelength = cb_obj.x;
const closest = source.data['wavelengths'].reduce(function(prev, curr) {
    return (Math.abs(curr - wavelength) < Math.abs(prev - wavelength) ? curr : prev);
});

const index = source.data['wavelengths'].indexOf(closest);
exp.text = String(source.data.exposure[index].toFixed(0))+' s';
snr.text = String(source.data.snr[index].toFixed(2));
wav.text = String((source.data.wavelengths[index]/1000).toFixed(3))+' \u03BCm';
flux.text = String(source.data.flux[index].toExponential(0))+' flam';
time.text = String(source.data.integration[index].toFixed(0))+' s';