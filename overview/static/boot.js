// Detecta si flexbox soporta "gap"; si no, activa los márgenes de respaldo (clase nfg).
// EN: Detects flexbox "gap" support; if missing, turns on the fallback margins (nfg class).
(function(){try{var d=document.createElement('div');d.style.cssText='display:flex;flex-direction:column;row-gap:1px;position:absolute;visibility:hidden';d.appendChild(document.createElement('div'));d.appendChild(document.createElement('div'));document.documentElement.appendChild(d);var ok=d.offsetHeight===1;document.documentElement.removeChild(d);if(!ok)document.documentElement.className+=' nfg'}catch(e){}})();
