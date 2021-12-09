// Input -- cb_obj = {name: oject_name, tags: [arbitrary_input], ...}
//          titles = { title: text, ...}


if (cb_obj.name === 'alert_container') {

    if (cb_obj.tags.length > 0) { 
        alert(cb_obj.tags[0]); 
        cb_obj.tags=[]; 
    }

} else if (cb_obj.name === 'cookie_container') {

    if (cb_obj.tags.length > 0) {
        const exp_date = new Date( new Date().getTime() + 1 * 24 * 60 * 60 * 1000 );  // Add 24 hours to current date
        const cookie_string = 'etcsettings=' + JSON.stringify(cb_obj.tags[0]) + '; expires=' + exp_date.toUTCString() + '; SameSite=Strict;';
        document.cookie = cookie_string;
        cb_obj.tags=[];
    }

} else if (cb_obj.name === 'page_loaded_container') {

    window.dispatchEvent(new Event("resize"));
    for (const title in titles) {
        if (document.querySelectorAll('.'+title+' label[data-tooltip]').length > 0){
            continue;
        }
        document.querySelectorAll('.'+title+' label, .'+title+' p, .'+title+' div.bk-slider-title').forEach( (label) =>{
            const info = document.createElement('label');
            info.setAttribute('data-tooltip', titles[title]);
            //info.appendChild(document.createTextNode('\U0001F6C8'));  // UTF-32
            info.appendChild(document.createTextNode('\uD83D\uDEC8'));  // UTF-16
            const line = document.createElement('div');
            line.classList.add('label-container');
            if (label.nodeName == 'P'){
                label.parentElement.classList.add('label-container');
                label.parentElement.parentElement.classList.add('paragraph-row');
            }
            label.parentElement.insertBefore(line, label);
            line.appendChild(label);
            line.appendChild(info);
            info.classList.add('info');
        });
    }

}