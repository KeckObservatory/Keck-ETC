// Input -- titles = { title: text, ...}

window.dispatchEvent(new Event("resize"));
for(const title in titles){
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
};