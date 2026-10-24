import {spawn} from 'node:child_process';
const browser=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',[
 '--headless=new','--disable-gpu','--incognito','--remote-debugging-address=127.0.0.1','--remote-debugging-port=9341',
 '--user-data-dir=C:/work/opnsense/otsa-rollback-demo-20261023/browser-profile',
 '--no-first-run','--no-default-browser-check','https://192.168.56.56/ui/core/snapshots'
],{windowsHide:true,stdio:'ignore'});
browser.on('exit',code=>console.log(JSON.stringify({browserExited:code})));
let ready=false;
for(let i=0;i<30;i++){
 try{const r=await fetch('http://127.0.0.1:9341/json/version');if(r.ok){ready=true;break}}catch{}
 await new Promise(r=>setTimeout(r,500));
}
console.log(JSON.stringify({debugReady:ready,browserPid:browser.pid}));
if(!ready){browser.kill();process.exit(1)}
const timer=setInterval(()=>{},1000);
process.on('SIGINT',()=>{clearInterval(timer);browser.kill();process.exit(0)});
