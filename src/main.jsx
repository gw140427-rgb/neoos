import React,{useEffect,useMemo,useRef,useState}from"react";
import{createRoot}from"react-dom/client";
import"./style.css";
const VERSION="NeoOS Web v1.1.0";
const COMMANDS=["help","clear","echo","date","time","calc","ls","touch","cat","write","append","rm","pwd","uname","version","whoami","neofetch","status","history","reboot","about","install","pkgs"];
function calc(input){const s=input.replace(/\s+/g,"");if(!s||!/^[0-9+*/%().-]+$/.test(s))throw Error();let i=0,peek=()=>s[i];const num=()=>{let st=i;while(/[0-9.]/.test(s[i]||""))i++;let n=Number(s.slice(st,i));if(!Number.isFinite(n))throw Error();return n};const factor=()=>{if(peek()==="-"){i++;return-num(factor())}if(peek()==="+"){i++;return num()}if(peek()==="("){i++;let v=expr();if(peek()!==")")throw Error();i++;return v}return num()};const term=()=>{let v=factor();while("*/%".includes(peek())){let op=s[i++],r=factor();if((op==="/"||op==="%")&&r===0)throw Error();v=op==="*"?v*r:op==="/" ?v/r:v%r}return v};const expr=()=>{let v=term();while("+-".includes(peek())){let op=s[i++],r=term();v=op==="+"?v+r:v-r}return v};let v=expr();if(i!==s.length||!Number.isFinite(v))throw Error();return String(v)}
function App(){
const[lines,setLines]=useState(["NEOOS WEB v1.1.0","NeoOS Web boot complete.","Type help to begin."]);
const[input,setInput]=useState("");
const[files,setFiles]=useState(()=>{try{return JSON.parse(localStorage.getItem("neoos-files")||'{"README.txt":"Welcome to NeoOS Web."}')}catch{return{"README.txt":"Welcome to NeoOS Web."}}});
const[history,setHistory]=useState(()=>{try{return JSON.parse(localStorage.getItem("neoos-history")||"[]")}catch{return[]}});
const[hi,setHi]=useState(-1),ref=useRef(null);
useEffect(()=>localStorage.setItem("neoos-files",JSON.stringify(files)),[files]);
useEffect(()=>localStorage.setItem("neoos-history",JSON.stringify(history.slice(-100))),[history]);
const names=useMemo(()=>Object.keys(files).sort(),[files]);
const print=x=>setLines(l=>[...l,...String(x).split("\n")]);
function run(raw){const line=raw.trim();if(!line)return;setHistory(h=>[...h,line].slice(-100));setHi(-1);if(line==="clear"){setLines([]);setInput("");return}print("neo@neoos:~$ "+line);const[p,...a]=line.split(/\s+/),arg=a.join(" ");let out="";
switch(p.toLowerCase()){
case"help":out="NeoOS Web commands:\n help clear echo date time calc\n ls touch cat write append rm\n pwd uname version whoami neofetch\n status history reboot about install pkgs";break;
case"echo":out=arg;break;case"date":out=new Date().toLocaleDateString("ko-KR");break;case"time":out=new Date().toLocaleString("ko-KR");break;
case"calc":try{out=calc(arg)}catch{out="계산 오류"}break;case"ls":out=names.join("\n")||"(파일 없음)";break;
case"touch":if(!a[0])out="사용법: touch 파일명";else{setFiles(f=>({...f,[a[0]]:f[a[0]]??""}));out=a[0]+" 생성됨"}break;
case"cat":out=a[0]in files?files[a[0]]:"cat: 파일 없음";break;
case"write":if(!a[0]||!a[1])out="사용법: write 파일명 내용";else{setFiles(f=>({...f,[a[0]]:a.slice(1).join(" ")}));out=a[0]+" 저장됨"}break;
case"append":if(!a[0]||!a[1])out="사용법: append 파일명 내용";else{setFiles(f=>({...f,[a[0]]:[f[a[0]]||"",a.slice(1).join(" ")].filter(Boolean).join("\n")}));out=a[0]+" 추가됨"}break;
case"rm":{let n=a[0]==="-f"?a[1]:a[0];if(!n||!(n in files))out="rm: 파일 없음";else{setFiles(f=>{let x={...f};delete x[n];return x});out=n+" 삭제됨"}break}
case"pwd":out="/home/guest";break;case"uname":out="NeoOS Web 1.1 • JavaScript • Vercel";break;case"version":out=VERSION;break;case"whoami":out="guest";break;
case"history":out=history.length?history.map((x,i)=>String(i+1).padStart(3," ")+"  "+x).join("\n"):"기록 없음";break;
case"neofetch":out="OS: NeoOS Web\nVersion: "+VERSION+"\nUser: guest\nShell: neo-shell\nFiles: "+names.length+"\nStorage: browser localStorage";break;
case"status":out="SYSTEM ONLINE\nShell: READY\nFiles: "+names.length+"\nSession: guest";break;
case"about":out="브라우저에서 실행되는 NeoOS 스타일 운영체제 시뮬레이터입니다.";break;
case"reboot":setLines([]);setTimeout(()=>setLines(["NeoOS Web rebooting...","","Boot complete.","Type help to begin."]),250);setInput("");return;
case"install":out=a[0]?"패키지 "+a[0]+" 설치됨 (웹 시뮬레이션)":"사용법: install 패키지명";break;
case"pkgs":out="neo-core\nneo-shell\nneo-utils";break;
case"login":case"logout":out="웹 버전은 guest 세션으로 실행됩니다.";break;
default:out="neo-shell: "+p+" 명령을 찾을 수 없습니다."}
print(out);setInput("")}
function key(e){if(e.key==="Enter"){run(input);return}if(e.key==="ArrowUp"){e.preventDefault();let n=Math.min(hi+1,history.length-1);setHi(n);setInput(history[history.length-1-n]||"")}if(e.key==="ArrowDown"){e.preventDefault();let n=hi-1;setHi(n);setInput(n<0?"":history[history.length-1-n]||"")}if(e.key==="Tab"){e.preventDefault();let m=COMMANDS.filter(x=>x.startsWith(input));if(m.length===1)setInput(m[0]+" ")}}
return <main onClick={()=>ref.current?.focus()}>
<header><div className="brand"><strong>NEO<span>OS</span></strong><small>WEB SYSTEM</small></div><div className="status"><i/> ONLINE</div></header>
<div className="layout"><section className="terminal"><div className="terminal-body">{lines.map((x,i)=><div className={x.startsWith("neo@neoos")?"command":""} key={i}>{x||"\u00a0"}</div>)}<div className="prompt"><span>neo@neoos:~$</span><input ref={ref} autoFocus spellCheck="false" value={input} onChange={e=>setInput(e.target.value)} onKeyDown={key}/></div></div></section>
<aside><div className="card"><h3>SYSTEM</h3><p><span>STATUS</span><b>ONLINE</b></p><p><span>USER</span><b>guest</b></p><p><span>FILES</span><b>{names.length}</b></p><p><span>VERSION</span><b>1.1.0</b></p></div><div className="card"><h3>QUICK COMMANDS</h3>{["help","neofetch","ls","status"].map(c=><button key={c} onClick={e=>{e.stopPropagation();run(c)}}>{c}</button>)}</div></aside></div>
<footer>{["help","ls","clear","reboot"].map(c=><button key={c} onClick={e=>{e.stopPropagation();run(c)}}>{c.toUpperCase()}</button>)}</footer>
</main>}
createRoot(document.getElementById("root")).render(<App/>);