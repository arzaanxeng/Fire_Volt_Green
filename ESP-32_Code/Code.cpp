/*
 * ═══════════════════════════════════════════════════════════════════
 *  ESP32  –  Wireless RC Car
 *  2× L298N  |  2× Single-Channel Relay (12V fans)  |  MQ-135 Gas Sensor
 *  Web-controlled via Access Point  →  http://192.168.4.1
 * ═══════════════════════════════════════════════════════════════════
 *
 *  Motor layout
 *  ┌──────────┐        ┌──────────┐
 *  │  L298N-A │        │  L298N-B │
 *  │ FL  │ RL │        │ FR  │ RR │
 *  └──────────┘        └──────────┘
 *   FL=Front-Left  RL=Rear-Left  FR=Front-Right  RR=Rear-Right
 * ═══════════════════════════════════════════════════════════════════
 */

#include <WiFi.h>
#include <WebServer.h>

// ─── Wi-Fi ────────────────────────────────────────────────────────
const char* SSID     = "ESP32_Car";
const char* PASSWORD = "12345678";

// ─── L298N-A  (LEFT: FL + RL) ─────────────────────────────────────
#define L_IN1  27
#define L_IN2  26
#define L_IN3  25
#define L_IN4  33
#define L_ENA  14
#define L_ENB  12

// ─── L298N-B  (RIGHT: FR + RR) ────────────────────────────────────
#define R_IN1   4
#define R_IN2   2
#define R_IN3  15
#define R_IN4  13
#define R_ENA  16
#define R_ENB  17

// ─── PWM ──────────────────────────────────────────────────────────
#define CH_FL 0
#define CH_RL 1
#define CH_FR 2
#define CH_RR 3
#define PWM_FREQ 1000
#define PWM_RES  8

int motorSpeed = 200;

// ─── Relays ───────────────────────────────────────────────────────
#define RELAY1    18
#define RELAY2    19
#define RELAY_ON  LOW
#define RELAY_OFF HIGH
bool fan1 = false, fan2 = false;

// ─── MQ-135 ───────────────────────────────────────────────────────
// AOUT → GPIO 34  (ADC1 channel, input-only, no pull-up needed)
// DOUT → GPIO 35  (optional digital threshold output from the module)
#define MQ135_AOUT  34
#define MQ135_DOUT  35   // set to -1 if you don't wire DOUT

// Thresholds (raw 12-bit ADC  0-4095)
// Calibrate these to your environment after warm-up (~3 min power-on)
#define GAS_CLEAN    800   // below  → CLEAN  (green)
#define GAS_MODERATE 1800  // below  → MODERATE (yellow)
#define GAS_HIGH     2800  // below  → HIGH  (orange)
                           // above  → DANGER  (red)

// Smoothing: running average over N samples
#define GAS_SAMPLES  10
int gasBuf[GAS_SAMPLES];
int gasIndex  = 0;
int gasSmooth = 0;

// ─────────────────────────────────────────────────────────────────
WebServer server(80);

// ═══════════════════════════════════════════════════════════════════
//  HTML
// ═══════════════════════════════════════════════════════════════════
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>ESP32 Car</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&display=swap');
:root{
  --bg:#0a0a0f;--panel:#111118;--border:#1e1e2e;
  --accent:#00f5a0;--accent2:#00d4f5;--danger:#f5003d;
  --warn:#f5a800;--orange:#f56a00;
  --text:#e0e0f0;--dim:#555577;--btn:#141422;--btn2:#1e1e35;
  --glow:0 0 18px rgba(0,245,160,.45);
  --glow2:0 0 18px rgba(0,212,245,.45);
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{
  background:var(--bg);color:var(--text);
  font-family:'Share Tech Mono',monospace;
  min-height:100vh;display:flex;flex-direction:column;
  align-items:center;justify-content:flex-start;
  padding:20px 20px 40px;overflow-x:hidden;
}
body::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:
    linear-gradient(rgba(0,245,160,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,245,160,.04) 1px,transparent 1px);
  background-size:40px 40px;
}
.wrap{position:relative;z-index:1;width:100%;max-width:420px;padding-top:12px}
header{text-align:center;margin-bottom:20px}
h1{
  font-family:'Orbitron',sans-serif;font-weight:900;
  font-size:clamp(1.25rem,5vw,1.85rem);letter-spacing:.12em;text-transform:uppercase;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.status{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:5px;
  font-size:.68rem;color:var(--dim);letter-spacing:.08em}
.dot{width:7px;height:7px;border-radius:50%;background:var(--accent);
  box-shadow:var(--glow);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

/* direction label */
.dirlabel{
  text-align:center;font-family:'Orbitron',sans-serif;font-size:.8rem;
  letter-spacing:.2em;text-transform:uppercase;color:var(--accent2);
  margin-bottom:16px;height:1.2em;text-shadow:var(--glow2);
}

/* D-pad */
.dpad{
  display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(3,1fr);
  gap:9px;aspect-ratio:1;width:min(265px,80vw);margin:0 auto 20px;
}
.btn{
  background:var(--btn);border:1px solid var(--border);border-radius:12px;
  color:var(--text);font-family:'Orbitron',sans-serif;font-size:1.4rem;
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:all .12s;user-select:none;-webkit-user-select:none;
  position:relative;overflow:hidden;
}
.btn::after{content:'';position:absolute;inset:0;opacity:0;transition:opacity .12s;
  background:radial-gradient(circle at center,rgba(0,245,160,.18),transparent 70%)}
.btn:active::after,.btn.active::after{opacity:1}
.btn:active,.btn.active{
  background:var(--btn2);border-color:var(--accent);color:var(--accent);
  box-shadow:var(--glow),inset 0 0 12px rgba(0,245,160,.1);transform:scale(.95)}
.btn.stop{border-color:var(--danger);color:var(--danger)}
.btn.stop:active,.btn.stop.active{box-shadow:0 0 18px rgba(245,0,61,.55);transform:scale(.95)}
.empty{visibility:hidden}

/* panels */
.panel{
  background:var(--panel);border:1px solid var(--border);
  border-radius:14px;padding:15px 17px;margin-bottom:13px;
}
.plabel{display:flex;justify-content:space-between;align-items:center;
  margin-bottom:11px;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.pval{font-family:'Orbitron',sans-serif;font-size:1rem;color:var(--accent);text-shadow:var(--glow)}
input[type=range]{-webkit-appearance:none;width:100%;height:4px;
  background:var(--border);border-radius:2px;outline:none}
input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;width:20px;height:20px;border-radius:50%;
  background:var(--accent);box-shadow:var(--glow);cursor:pointer;transition:transform .1s}
input[type=range]::-webkit-slider-thumb:active{transform:scale(1.25)}

/* fan buttons */
.fans{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.fbtn{
  background:var(--btn);border:1px solid var(--border);border-radius:12px;
  color:var(--text);font-family:'Share Tech Mono',monospace;
  padding:13px 8px;cursor:pointer;display:flex;flex-direction:column;
  align-items:center;gap:4px;transition:all .15s;}
.ficon{font-size:1.3rem;color:var(--dim);display:inline-block;transition:color .2s}
.fname{font-size:.67rem;letter-spacing:.12em;text-transform:uppercase;color:var(--dim)}
.fstatus{font-family:'Orbitron',sans-serif;font-size:.7rem;
  letter-spacing:.15em;color:var(--danger);transition:color .2s}
.fbtn.on{border-color:var(--accent);box-shadow:var(--glow),inset 0 0 14px rgba(0,245,160,.07)}
.fbtn.on .ficon{color:var(--accent);animation:spin 1.1s linear infinite}
.fbtn.on .fstatus{color:var(--accent)}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── MQ-135 gas panel ── */
.gas-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.gas-title{font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.gas-badge{
  font-family:'Orbitron',sans-serif;font-size:.7rem;letter-spacing:.12em;
  padding:3px 10px;border-radius:20px;border:1px solid;transition:all .4s;
}
.gas-badge.clean   {color:#00f5a0;border-color:#00f5a0;text-shadow:0 0 8px rgba(0,245,160,.6)}
.gas-badge.moderate{color:#f5e000;border-color:#f5e000;text-shadow:0 0 8px rgba(245,224,0,.6)}
.gas-badge.high    {color:#f5a800;border-color:#f5a800;text-shadow:0 0 8px rgba(245,168,0,.6)}
.gas-badge.danger  {color:#f5003d;border-color:#f5003d;text-shadow:0 0 8px rgba(245,0,61,.7);
  animation:blink .7s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}

/* big value */
.gas-reading{
  display:flex;align-items:baseline;gap:6px;margin-bottom:14px;
}
.gas-value{
  font-family:'Orbitron',sans-serif;font-size:2.4rem;font-weight:900;
  transition:color .4s;line-height:1;
}
.gas-unit{font-size:.7rem;color:var(--dim);letter-spacing:.08em}

/* segmented bar */
.gas-bar-wrap{position:relative;height:10px;border-radius:5px;
  background:var(--border);overflow:hidden;margin-bottom:10px}
.gas-bar-fill{
  height:100%;border-radius:5px;width:0%;
  transition:width .5s ease, background .5s ease;
}
.gas-segments{
  position:absolute;inset:0;display:flex;pointer-events:none;
}
.gas-seg{flex:1;border-right:1px solid rgba(0,0,0,.4)}
.gas-seg:last-child{border-right:none}

/* tick labels under bar */
.gas-ticks{display:flex;justify-content:space-between;
  font-size:.58rem;color:var(--dim);margin-top:5px;letter-spacing:.05em}

/* sparkline */
.spark-wrap{margin-top:10px}
.spark-label{font-size:.6rem;color:var(--dim);letter-spacing:.08em;margin-bottom:4px;
  text-transform:uppercase}
canvas#spark{width:100%;height:44px;display:block}

.hint{text-align:center;font-size:.62rem;color:var(--dim);letter-spacing:.07em;margin-top:6px}
</style>
</head>
<body>
<div class="wrap">

  <header>
    <h1>RC Car Control</h1>
    <div class="status"><div class="dot"></div>
      <span>CONNECTED &bull; ESP32 &bull; MQ-135</span></div>
  </header>

  <div class="dirlabel" id="dir">STANDBY</div>

  <!-- D-pad -->
  <div class="dpad">
    <div class="empty"></div>
    <button class="btn" id="bf"
      ontouchstart="go('forward')" ontouchend="go('stop')"
      onmousedown="go('forward')"  onmouseup="go('stop')">&#9650;</button>
    <div class="empty"></div>
    <button class="btn" id="bl"
      ontouchstart="go('left')"  ontouchend="go('stop')"
      onmousedown="go('left')"   onmouseup="go('stop')">&#9664;</button>
    <button class="btn stop" id="bs" onclick="go('stop')">&#9632;</button>
    <button class="btn" id="br"
      ontouchstart="go('right')" ontouchend="go('stop')"
      onmousedown="go('right')"  onmouseup="go('stop')">&#9654;</button>
    <div class="empty"></div>
    <button class="btn" id="bb"
      ontouchstart="go('backward')" ontouchend="go('stop')"
      onmousedown="go('backward')"  onmouseup="go('stop')">&#9660;</button>
    <div class="empty"></div>
  </div>

  <!-- speed -->
  <div class="panel">
    <div class="plabel">
      <span>Motor Speed</span>
      <span class="pval" id="spv">200</span>
    </div>
    <input type="range" min="80" max="255" value="200" oninput="setSpd(this.value)">
  </div>

  <!-- fans -->
  <div class="panel">
    <div class="plabel" style="margin-bottom:14px">
      <span>Fan Control</span>
      <span style="font-size:.62rem;color:var(--dim)">12V DC &bull; Relay</span>
    </div>
    <div class="fans">
      <button class="fbtn" id="f1" onclick="fan(1)">
        <span class="ficon">&#9670;</span>
        <span class="fname">Fan 1</span>
        <span class="fstatus" id="fs1">OFF</span>
      </button>
      <button class="fbtn" id="f2" onclick="fan(2)">
        <span class="ficon">&#9670;</span>
        <span class="fname">Fan 2</span>
        <span class="fstatus" id="fs2">OFF</span>
      </button>
    </div>
  </div>

  <!-- ── MQ-135 Gas Sensor Panel ───────────────────────────────── -->
  <div class="panel" id="gasPanel">
    <div class="gas-header">
      <span class="gas-title">Filter / Gas Monitor &bull; MQ-135</span>
      <span class="gas-badge clean" id="gasBadge">CLEAN</span>
    </div>

    <div class="gas-reading">
      <span class="gas-value" id="gasVal" style="color:var(--accent)">---</span>
      <span class="gas-unit">/ 4095 ADC</span>
    </div>

    <!-- segmented colour bar -->
    <div class="gas-bar-wrap">
      <div class="gas-bar-fill" id="gasBar"></div>
      <!-- 4 zone overlays -->
      <div class="gas-segments">
        <div class="gas-seg" style="background:rgba(0,245,160,.08)"></div>
        <div class="gas-seg" style="background:rgba(245,224,0,.06)"></div>
        <div class="gas-seg" style="background:rgba(245,168,0,.06)"></div>
        <div class="gas-seg" style="background:rgba(245,0,61,.06)"></div>
      </div>
    </div>
    <div class="gas-ticks">
      <span>0</span>
      <span style="color:#00f5a0">CLEAN</span>
      <span style="color:#f5e000">MOD</span>
      <span style="color:#f5a800">HIGH</span>
      <span style="color:#f5003d">DANGER</span>
      <span>4095</span>
    </div>

    <!-- sparkline history -->
    <div class="spark-wrap">
      <div class="spark-label">History (last 60 s)</div>
      <canvas id="spark" width="380" height="44"></canvas>
    </div>
  </div>

  <div class="hint">Arrow / WASD keys on desktop &bull; Hold to keep moving</div>
</div>

<script>
/* ── motion controls ── */
const dirEl=document.getElementById('dir'),spvEl=document.getElementById('spv');
const LABELS={forward:'FORWARD',backward:'REVERSE',left:'TURN LEFT',right:'TURN RIGHT',stop:'STANDBY'};
const BMAP={forward:'bf',backward:'bb',left:'bl',right:'br',stop:'bs'};
function go(a){
  fetch('/cmd?action='+a).catch(()=>{});
  dirEl.textContent=LABELS[a]||'';
  document.querySelectorAll('.btn').forEach(b=>b.classList.remove('active'));
  if(BMAP[a])document.getElementById(BMAP[a]).classList.add('active');
  if(a==='stop')setTimeout(()=>document.getElementById('bs').classList.remove('active'),200);
}
function setSpd(v){spvEl.textContent=v;fetch('/speed?val='+v).catch(()=>{});}

/* ── fans ── */
const fanOn={1:false,2:false};
function fan(n){
  fanOn[n]=!fanOn[n];
  fetch('/relay?fan='+n+'&state='+(fanOn[n]?'on':'off')).catch(()=>{});
  document.getElementById('f'+n).classList.toggle('on',fanOn[n]);
  document.getElementById('fs'+n).textContent=fanOn[n]?'ON':'OFF';
}

/* ── keyboard ── */
const KM={ArrowUp:'forward',ArrowDown:'backward',ArrowLeft:'left',ArrowRight:'right',
          ' ':'stop',w:'forward',s:'backward',a:'left',d:'right'};
const held={};
document.addEventListener('keydown',e=>{const a=KM[e.key];if(a&&!held[e.key]){held[e.key]=1;go(a);e.preventDefault();}});
document.addEventListener('keyup',e=>{if(KM[e.key]){delete held[e.key];go('stop');}});
window.addEventListener('keydown',e=>{
  if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(e.key))e.preventDefault();
},{passive:false});

/* ════════════════════════════════════════════════════════
   MQ-135  live polling
   ════════════════════════════════════════════════════════ */
const THRESHOLDS = {clean:800, moderate:1800, high:2800, max:4095};
const COLORS     = {clean:'#00f5a0', moderate:'#f5e000', high:'#f5a800', danger:'#f5003d'};

const gasValEl  = document.getElementById('gasVal');
const gasBarEl  = document.getElementById('gasBar');
const gasBadge  = document.getElementById('gasBadge');

/* sparkline */
const SPARK_MAX = 60;          // keep last 60 readings (~60 s at 1 s interval)
const sparkData = [];
const cvs = document.getElementById('spark');
const ctx = cvs.getContext('2d');

function drawSpark(){
  const W=cvs.offsetWidth*devicePixelRatio||380, H=44*devicePixelRatio||44;
  cvs.width=W; cvs.height=H;
  ctx.clearRect(0,0,W,H);
  if(sparkData.length<2) return;
  const step = W/(SPARK_MAX-1);
  ctx.beginPath();
  sparkData.forEach((v,i)=>{
    const x=i*step;
    const y=H - (v/4095)*H;
    i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
  });
  // gradient stroke
  const grad=ctx.createLinearGradient(0,0,W,0);
  grad.addColorStop(0,'rgba(0,245,160,.3)');
  grad.addColorStop(0.5,'rgba(245,224,0,.6)');
  grad.addColorStop(1,'rgba(245,0,61,.8)');
  ctx.strokeStyle=grad;
  ctx.lineWidth=1.5*devicePixelRatio;
  ctx.stroke();
  // fill under
  ctx.lineTo(sparkData.length*step-step,H);
  ctx.lineTo(0,H);
  ctx.closePath();
  ctx.fillStyle='rgba(0,245,160,.04)';
  ctx.fill();
}

function classify(v){
  if(v < THRESHOLDS.clean)    return 'clean';
  if(v < THRESHOLDS.moderate) return 'moderate';
  if(v < THRESHOLDS.high)     return 'high';
  return 'danger';
}

const BADGE_TEXT={clean:'CLEAN',moderate:'MODERATE',high:'HIGH GAS',danger:'DANGER!'};

function updateGasUI(raw){
  const level = classify(raw);
  const col   = COLORS[level];
  const pct   = Math.min(raw/4095*100, 100).toFixed(1);

  gasValEl.textContent = raw;
  gasValEl.style.color = col;
  gasBarEl.style.width = pct+'%';
  gasBarEl.style.background = col;
  gasBarEl.style.boxShadow  = '0 0 10px '+col+'99';

  gasBadge.className = 'gas-badge '+level;
  gasBadge.textContent = BADGE_TEXT[level];

  // sparkline
  sparkData.push(raw);
  if(sparkData.length>SPARK_MAX) sparkData.shift();
  drawSpark();
}

async function pollGas(){
  try{
    const r = await fetch('/gas');
    const j = await r.json();
    updateGasUI(j.raw);
  } catch(e){}
}

pollGas();
setInterval(pollGas, 1000);   // poll every 1 second
</script>
</body>
</html>
)rawliteral";


// ═══════════════════════════════════════════════════════════════════
//  MQ-135  –  running average
// ═══════════════════════════════════════════════════════════════════
void initGasBuf() {
  int raw = analogRead(MQ135_AOUT);
  for (int i = 0; i < GAS_SAMPLES; i++) gasBuf[i] = raw;
  gasSmooth = raw;
}

void updateGas() {
  gasBuf[gasIndex] = analogRead(MQ135_AOUT);
  gasIndex = (gasIndex + 1) % GAS_SAMPLES;
  long sum = 0;
  for (int i = 0; i < GAS_SAMPLES; i++) sum += gasBuf[i];
  gasSmooth = (int)(sum / GAS_SAMPLES);
}

const char* gasLevel() {
  if (gasSmooth < GAS_CLEAN)    return "CLEAN";
  if (gasSmooth < GAS_MODERATE) return "MODERATE";
  if (gasSmooth < GAS_HIGH)     return "HIGH";
  return "DANGER";
}


// ═══════════════════════════════════════════════════════════════════
//  Motor helpers
// ═══════════════════════════════════════════════════════════════════
void setLeft(int dir, int spd) {
  bool a=(dir==1),b=(dir==-1);
  digitalWrite(L_IN1,a); digitalWrite(L_IN2,b);
  digitalWrite(L_IN3,a); digitalWrite(L_IN4,b);
  ledcWrite(CH_FL,spd); ledcWrite(CH_RL,spd);
}
void setRight(int dir, int spd) {
  bool a=(dir==1),b=(dir==-1);
  digitalWrite(R_IN1,a); digitalWrite(R_IN2,b);
  digitalWrite(R_IN3,a); digitalWrite(R_IN4,b);
  ledcWrite(CH_FR,spd); ledcWrite(CH_RR,spd);
}
void moveForward()  { setLeft( 1,motorSpeed); setRight( 1,motorSpeed); }
void moveBackward() { setLeft(-1,motorSpeed); setRight(-1,motorSpeed); }
void turnLeft()     { setLeft(-1,motorSpeed); setRight( 1,motorSpeed); }
void turnRight()    { setLeft( 1,motorSpeed); setRight(-1,motorSpeed); }
void stopCar()      { setLeft( 0,0);          setRight( 0,0);          }


// ═══════════════════════════════════════════════════════════════════
//  Relay helper
// ═══════════════════════════════════════════════════════════════════
void setRelay(uint8_t pin, bool &state, bool on) {
  state = on;
  digitalWrite(pin, on ? RELAY_ON : RELAY_OFF);
}


// ═══════════════════════════════════════════════════════════════════
//  HTTP handlers
// ═══════════════════════════════════════════════════════════════════
void handleRoot()  { server.send_P(200,"text/html",INDEX_HTML); }

void handleCmd() {
  if(!server.hasArg("action")){ server.send(400,"text/plain","missing action"); return; }
  String a=server.arg("action");
  if      (a=="forward")  moveForward();
  else if (a=="backward") moveBackward();
  else if (a=="left")     turnLeft();
  else if (a=="right")    turnRight();
  else if (a=="stop")     stopCar();
  server.send(200,"text/plain","OK");
}

void handleSpeed() {
  if(!server.hasArg("val")){ server.send(400,"text/plain","missing val"); return; }
  motorSpeed=constrain(server.arg("val").toInt(),0,255);
  server.send(200,"text/plain","OK");
}

void handleRelay() {
  if(!server.hasArg("fan")||!server.hasArg("state")){
    server.send(400,"text/plain","missing args"); return; }
  int  n =server.arg("fan").toInt();
  bool on=(server.arg("state")=="on");
  if      (n==1) setRelay(RELAY1,fan1,on);
  else if (n==2) setRelay(RELAY2,fan2,on);
  else { server.send(400,"text/plain","invalid fan"); return; }
  server.send(200,"text/plain","OK");
}

// Returns JSON:  {"raw":1234,"level":"MODERATE","dout":0}
void handleGas() {
  updateGas();   // take a fresh sample right on request
  int dout = (MQ135_DOUT >= 0) ? digitalRead(MQ135_DOUT) : -1;
  String json = "{\"raw\":";
  json += gasSmooth;
  json += ",\"level\":\"";
  json += gasLevel();
  json += "\",\"dout\":";
  json += dout;
  json += "}";
  server.sendHeader("Cache-Control","no-cache");
  server.send(200,"application/json",json);
}


// ═══════════════════════════════════════════════════════════════════
//  Setup
// ═══════════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);

  // L298N-A
  pinMode(L_IN1,OUTPUT); pinMode(L_IN2,OUTPUT);
  pinMode(L_IN3,OUTPUT); pinMode(L_IN4,OUTPUT);

  // L298N-B
  pinMode(R_IN1,OUTPUT); pinMode(R_IN2,OUTPUT);
  pinMode(R_IN3,OUTPUT); pinMode(R_IN4,OUTPUT);

  // PWM
  // ledcSetup(CH_FL,PWM_FREQ,PWM_RES); ledcAttachPin(L_ENA,CH_FL);
  // ledcSetup(CH_RL,PWM_FREQ,PWM_RES); ledcAttachPin(L_ENB,CH_RL);
  // ledcSetup(CH_FR,PWM_FREQ,PWM_RES); ledcAttachPin(R_ENA,CH_FR);
  // ledcSetup(CH_RR,PWM_FREQ,PWM_RES); ledcAttachPin(R_ENB,CH_RR);
  stopCar();

  // Relays OFF
  pinMode(RELAY1,OUTPUT); digitalWrite(RELAY1,RELAY_OFF);
  pinMode(RELAY2,OUTPUT); digitalWrite(RELAY2,RELAY_OFF);

  // MQ-135
  analogReadResolution(12);         // 12-bit → 0-4095
  analogSetAttenuation(ADC_11db);   // 0-3.3 V range
  if(MQ135_DOUT >= 0) pinMode(MQ135_DOUT, INPUT);
  initGasBuf();
  Serial.println("MQ-135 ready. Warm-up ~3 min for accurate readings.");

  // Wi-Fi AP
  WiFi.softAP(SSID,PASSWORD);
  Serial.print("AP IP: "); Serial.println(WiFi.softAPIP());

  // Routes
  server.on("/",      handleRoot);
  server.on("/cmd",   handleCmd);
  server.on("/speed", handleSpeed);
  server.on("/relay", handleRelay);
  server.on("/gas",   handleGas);
  server.begin();
  Serial.println("Ready → http://192.168.4.1");
}


// ═══════════════════════════════════════════════════════════════════
//  Loop
// ═══════════════════════════════════════════════════════════════════

unsigned long lastGasSample = 0;

void loop() {
  server.handleClient();

  // Background gas sampling every 200 ms (smoothing buffer)
  if(millis() - lastGasSample > 200) {
    lastGasSample = millis();
    int raw = analogRead(MQ135_AOUT);
    gasBuf[gasIndex] = raw;
    gasIndex = (gasIndex + 1) % GAS_SAMPLES;
    long sum=0;
    for(int i=0;i<GAS_SAMPLES;i++) sum+=gasBuf[i];
    gasSmooth=(int)(sum/GAS_SAMPLES);
    Serial.printf("MQ135 raw=%d smooth=%d level=%s\n", raw, gasSmooth, gasLevel());
  }
}
