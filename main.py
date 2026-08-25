import pygame, sys, math, random, textwrap, array
pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
except pygame.error:
    pass

# RECEIVER // BUILD 0.7.6.3 FINAL MOBILE
# Portrait / touchscreen-first fan prototype
info=pygame.display.Info()
W=max(720,info.current_w); H=max(1180,info.current_h)
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption("RECEIVER // Build 0.7.6.3 FINAL")
clock=pygame.time.Clock()

BASE_W,BASE_H=1080,1920
SCALE=min(W/BASE_W,H/BASE_H)
def sc(v): return max(1,int(v*SCALE))

SMALL=pygame.font.Font(None,sc(22))
FONT=pygame.font.Font(None,sc(28))
BIG=pygame.font.Font(None,sc(42))
HUGE=pygame.font.Font(None,sc(55))
BIG.set_bold(True)
HUGE.set_bold(True)

BG=(7,9,12); PANEL=(17,22,25); PANEL2=(26,34,38)
TXT=(194,231,207); DIM=(91,125,110); WHITE=(235,245,239)
WARN=(235,195,95); BAD=(220,80,80)

def tone(freq=440,ms=80,vol=.14,noise=0):
    if not pygame.mixer.get_init(): return None
    rate=22050;n=max(1,int(rate*ms/1000));a=array.array("h")
    for i in range(n):
        t=i/rate
        s=math.sin(2*math.pi*freq*t)
        if noise:s=(1-noise)*s+noise*random.uniform(-1,1)
        edge=min(1,i/max(1,n*.08),(n-i-1)/max(1,n*.08))
        a.append(int(32767*vol*s*max(0,edge)))
    return pygame.mixer.Sound(buffer=a.tobytes())
CLICK=tone(520,45,.10); BEEP=tone(760,90,.14); WARN_S=tone(220,180,.18)
CONTACT=tone(1200,130,.14,.3); LOCK=tone(880,380,.15,.05); LOW=tone(110,500,.12,.08)
HOST_HUM=tone(145,650,.055,.03)
HOST_REPLY=tone(930,170,.13,.05)
HOST_PAIN=tone(310,280,.20,.55)
HOST_HELP=tone(660,520,.14,.02)
ENGINE=tone(185,700,.10,.08)
MIRACLE=tone(720,700,.14,.02)
CASH=tone(1180,90,.14);
def snd(s):
    if s:
        try:s.play()
        except:pass

def make_title_ambience(ms=9000):
    """Original sparse tinny / strange-space ambience for the title screen."""
    if not pygame.mixer.get_init():
        return None

    rate=22050
    n=max(1,int(rate*ms/1000))
    a=array.array("h")

    # Intentionally thin, metallic and mostly empty.
    ping_events=[
        (0.9, 1370, .17),
        (2.6, 1810, .11),
        (4.7, 1120, .15),
        (6.1, 2240, .08),
        (7.7, 1540, .13),
    ]

    for i in range(n):
        t=i/rate

        # Barely audible distant carrier.
        carrier=math.sin(2*math.pi*41*t + math.sin(t*.18)*1.8)*0.045

        # Thin detuned metallic partials with slow phase drift.
        tin1=math.sin(2*math.pi*(523.0+math.sin(t*.21)*2.5)*t)*0.027
        tin2=math.sin(2*math.pi*(947.0+math.sin(t*.13)*4.0)*t+1.7)*0.018
        tin3=math.sin(2*math.pi*(1733.0+math.sin(t*.07)*8.0)*t+.4)*0.010

        # Sparse short decaying "space pings".
        ping=0.0
        for centre,freq,amp in ping_events:
            d=t-centre
            if 0 <= d < .48:
                env=math.exp(-d*8.5)
                wobble=1.0+0.015*math.sin(d*21)
                ping += math.sin(2*math.pi*freq*wobble*d)*amp*env

        # Occasional narrow-band static shimmer.
        shimmer=(random.uniform(-1,1)*0.006) * (0.35+0.65*(0.5+0.5*math.sin(t*.41)))

        # Lots of negative space: slow amplitude breathing.
        gate=0.34 + 0.30*(0.5+0.5*math.sin(t*.36-1.2))
        sample=(carrier + (tin1+tin2+tin3)*gate + ping + shimmer)

        a.append(int(max(-1,min(1,sample))*32767*.42))

    return pygame.mixer.Sound(buffer=a.tobytes())

TITLE_AMBIENCE=make_title_ambience()
title_channel=None
title_transition=False
title_transition_t=0.0
title_transition_duration=0.75

mode="TITLE"
freq=41; phase=25; strength=20; selected="COMPUTATIONAL"
knowledge=0; wildlife=100.; human=100.; anomaly=0.
bio_auth=False; neural_auth=False; vessel_auth=False
experiment=False; etime=0.; post_persist=0.
discoveries=set(); records=[]
vessel_parts={"LOGIC":0,"BIOLOGY":0,"NEURAL":0,"STABILITY":0}
vessel_built=False; vessel_viable=False; persistence=0.
hidden_stage=1
sync=[17,64,39]; sync_locked=False
reception=0.; reception_active=False; reception_done=False
agency_stage=0; agency_timer=0.; ending=False
flash_white=0.; flash_red=0.; alarm=0.

# Build 0.6 extension state. Existing 0.5.1 systems remain intact.
host_unlocked=False
host_tests={"VISUAL":0,"AUDIO":0,"MECHANICAL":0,"ELECTRICAL":0}
host_response=0.
host_trust=0.
host_hum_timer=0.
host_comm_stage=0
host_comm_timer=0.
facility_failure=False
facility_integrity=100.
host_helped=False
applications_unlocked=False
applications_done=0
applications_completed=set()
project_revealed=False
build6_ending=False

# Build 0.7 final act
engine_unlocked=False
engine_parts={"INTERFACE":0,"AMPLIFIER":0,"ROUTING":0,"STABILISER":0}
engine_built=False
engine_output=15
engine_draws=0
miracles_done=set()
human_restoring=False
wildlife_restoring=False  # retained for compatibility; no longer used
restoration_load=0.
final_choice=False
ending_route=None
ending_timer=0.
credits_active=False
credits_timer=0.

# Final mobile/navigation fixes
engineering_data=0
buttons=[]
logs=["FACILITY ONLINE.","Directive: characterise archived contact."]

subs={"COMPUTATIONAL":(.92,.05,.18,.82),"MECHANICAL":(.65,0,.02,.95),
      "BIOLOGICAL":(.12,.90,.38,.46),"NEURAL":(.42,.82,.95,.31)}

def wrap(text,font,width):
    words=text.split();out=[];cur=""
    for w in words:
        q=(cur+" "+w).strip()
        if font.size(q)[0]<=width:cur=q
        else:
            if cur:out.append(cur)
            cur=w
    if cur:out.append(cur)
    return out
def para(text,x,y,width,col=TXT,font=None):
    font=font or SMALL
    for line in wrap(text,font,width):
        screen.blit(font.render(line,True,col),(x,y));y+=font.get_height()+sc(7)
    return y
def log(x):
    logs.append(x)
    if len(logs)>18:logs.pop(0)
def record(x):
    if x not in records:records.append(x);log("ARCHIVE UPDATED.")
def button(rect,label,action,en=True,accent=False,font=None):
    r=pygame.Rect(rect);buttons.append((r,action,en))
    pygame.draw.rect(screen,PANEL2 if en else PANEL,r,border_radius=sc(14))
    pygame.draw.rect(screen,WHITE if accent and en else DIM,r,sc(2),border_radius=sc(14))
    f=font or SMALL;t=f.render(label,True,WHITE if en else DIM)
    screen.blit(t,(r.centerx-t.get_width()/2,r.centery-t.get_height()/2))
def title(t,sub="",back=True):
    screen.blit(BIG.render(t,True,WHITE),(sc(28),sc(22)))
    if sub:screen.blit(SMALL.render(sub,True,DIM),(sc(30),sc(78)))
    if back:button((W-sc(230),sc(18),sc(195),sc(68)),"FACILITY","HOME",True,True)
def available(n):
    return not(n=="BIOLOGICAL" and not bio_auth) and not(n=="NEURAL" and not neural_auth)
def compat(p):
    tune=max(0,1-abs(freq-73)/62)*max(0,1-abs(phase-61)/76)
    substrate=.22*p[0]+.27*p[1]+.36*p[2]+.15*p[3]
    return max(0,min(1,tune*substrate*(strength/100)**.52))
def vt():
    return tuple(vessel_parts[k]/100 for k in ["LOGIC","BIOLOGY","NEURAL","STABILITY"])
def sync_score():
    return max(0,100-sum(abs(v-61) for v in sync)/3*1.65)

def complete_experiment():
    global experiment,knowledge,bio_auth,neural_auth,vessel_auth,anomaly,post_persist,hidden_stage
    p=subs[selected];c=compat(p);experiment=False
    knowledge+=max(2,int(c*18+etime/5))
    record(f"{selected}: coherence {int(c*100)}%, exposure {etime:.1f}s.")
    if c>.24:discoveries.add("logic");record("Repeatable logical interruption confirmed.")
    if selected=="COMPUTATIONAL" and c>.32 and etime>8:
        bio_auth=True;record("Living substrate testing authorised.")
    if selected=="BIOLOGICAL" and c>.34 and etime>10:
        discoveries.add("bio");neural_auth=True;record("Living tissue receives the pattern.")
    if selected=="NEURAL" and c>.42 and etime>12:
        discoveries.add("neural");record("Neural activity synchronises with contact.")
    if selected=="NEURAL" and c>.52 and etime>18:
        discoveries.add("persistence");post_persist=min(6,.5+c*5);record("Pattern persists after cutoff.")
    if {"logic","bio","neural","persistence"}.issubset(discoveries):
        vessel_auth=True;record("HOST PROGRAM AUTHORISED.")
    if wildlife<70:hidden_stage=max(hidden_stage,2)
    anomaly=max(anomaly,c*min(1,etime/25));snd(BEEP)

def startstop():
    global experiment,etime
    if hidden_stage>=4:return
    if experiment:complete_experiment()
    else:experiment=True;etime=0;log("EXPOSURE STARTED // "+selected);snd(CLICK)

def assess_vessel():
    global vessel_built,vessel_viable,persistence
    vessel_built=True
    p=vt();bal=min(p);c=compat(p)
    persistence=max(0,(c*.7+bal*.55-.48)*100)
    vessel_viable=bal>=.6 and c>=.58 and persistence>=30
    log("HOST ASSEMBLED // diagnostic running.")
    record("Mechanical host assembled from learned reception properties.")
    if vessel_viable:record("HOST STATUS: VIABLE // stable reception predicted.");snd(LOCK)
    else:record("HOST STATUS: INCOMPLETE // improve balance/coherence.");snd(WARN_S)

def hosttest():
    global knowledge,persistence,vessel_viable
    c=compat(vt());bal=min(vt())
    persistence=max(0,(c*.7+bal*.55-.48)*100);knowledge+=int(c*6)
    vessel_viable=bal>=.6 and c>=.58 and persistence>=30
    log(f"HOST TEST // coherence {int(c*100)}% // persistence {persistence/8:.1f}s")
    snd(CONTACT if vessel_viable else BEEP)

def handle(a):
    global mode,selected,freq,phase,strength,knowledge,vessel_built
    global sync_locked,reception_active,flash_white,running
    global host_response,host_trust,host_comm_stage,host_comm_timer
    global host_helped,applications_unlocked,facility_integrity
    global applications_done,applications_completed,project_revealed,build6_ending
    global engine_unlocked
    global engine_built,engine_output,engine_draws,human_restoring,wildlife_restoring
    global final_choice,ending_route,ending_timer,credits_active,credits_timer
    global engineering_data
    if a=="QUIT":running=False;return
    if a in ("HOME","SIGNAL","SUBSTRATE","OBS","ARCHIVE","VESSEL","ENV","SYNC","RECEPTION","HOST","APPLICATIONS","ENGINE","SYSTEMS"):
        if a=="VESSEL" and not vessel_auth:log("VESSEL LAB SEALED.");snd(WARN_S);return
        if a=="SYNC" and hidden_stage<4:log("SYNCHRONISATION ARRAY OFFLINE.");return
        if a=="RECEPTION" and not sync_locked:return
        if a=="HOST" and not host_unlocked:return
        if a=="APPLICATIONS" and not applications_unlocked:return
        if a=="ENGINE" and not engine_unlocked:return
        mode=a;snd(CLICK);return
    if a.startswith("SUB:"):
        n=a.split(":",1)[1]
        if available(n) and not experiment:selected=n;snd(CLICK)
    elif a=="EXPOSE":startstop()
    elif a.startswith("FREQ:"):freq=int(a.split(":")[1]);snd(CLICK)
    elif a.startswith("PHASE:"):phase=int(a.split(":")[1]);snd(CLICK)
    elif a.startswith("STRENGTH:"):strength=int(a.split(":")[1]);snd(CLICK)
    elif a.startswith("PART:"):
        n=a.split(":")[1]
        if knowledge>=5:vessel_parts[n]=min(100,vessel_parts[n]+10);knowledge-=5;snd(CLICK)
    elif a=="ASSEMBLE":assess_vessel()
    elif a=="HOSTTEST":hosttest()
    elif a.startswith("SYNC:"):
        i,v=a.split(":")[1:];sync[int(i)]=int(v);snd(CLICK)
        if sync_score()>=96:
            if not vessel_built or not vessel_viable:
                log("ALIGNMENT ACHIEVED // NO VIABLE RECEIVER.")
                record("Connection alignment possible, but host cannot safely receive.")
                snd(WARN_S)
            else:
                sync_locked=True;flash_white=.5;record("Connection stabilised. Viable host awaiting reception.");snd(LOCK)
    elif a.startswith("HOSTSTIM:"):
        kind=a.split(":",1)[1]
        host_tests[kind]+=1
        host_comm_timer=0.
        if kind=="ELECTRICAL":
            host_response=min(100.,host_response+32)
            host_trust=max(-100.,host_trust-12)
            record("Aversive electrical stimulus produced an immediate structured response.")
            log("HOST RESPONSE // HIGH AMPLITUDE")
            snd(HOST_PAIN)
        elif kind=="MECHANICAL":
            host_response=min(100.,host_response+14)
            host_trust=max(-100.,host_trust-2)
            record("Mechanical stimulus registered.")
            snd(CONTACT)
        elif kind=="AUDIO":
            host_response=min(100.,host_response+18)
            host_trust=min(100.,host_trust+4)
            record("Audio/signal stimulus produced repeatable patterned output.")
            snd(HOST_REPLY)
        elif kind=="VISUAL":
            host_response=min(100.,host_response+12)
            host_trust=min(100.,host_trust+3)
            record("Visual information registered by local host.")
            snd(BEEP)

        total=sum(host_tests.values())
        if host_tests["ELECTRICAL"]>=1 and total>=3 and host_comm_stage<1:
            host_comm_stage=1
            record("Subject appears capable of aversive experience.")
        if (host_tests["AUDIO"]>=2 or host_tests["VISUAL"]>=3) and host_comm_stage<2:
            host_comm_stage=2
            record("Structured stimulus-response protocol established.")

    elif a=="HOST_HELP":
        if facility_failure and not host_helped:
            host_helped=True
            facility_integrity=100.
            applications_unlocked=True
            record("Unauthorised host intervention restored facility power regulation.")
            record("APPLICATIONS PROGRAM AUTHORISED.")
            snd(HOST_HELP)

    elif a.startswith("APP:"):
        target=a.split(":",1)[1]

        # Each application is a one-time successful intervention.
        if target in applications_completed:
            log(f"APPLICATION ALREADY COMPLETE // {target}")
            snd(CLICK)
            return

        applications_completed.add(target)
        applications_done=len(applications_completed)
        engineering_data+=20
        record(f"HOST APPLICATION // {target} // intervention successful.")
        record("ENGINEERING DATA +20")
        snd(HOST_HELP)

        if applications_done>=3 and not project_revealed:
            project_revealed=True
            engine_unlocked=True
            record("NEW PROJECT AUTHORISATION // HOST INTEGRATION PROGRAM.")
            record("DESIGNATION: ANGEL ENGINE")
            build6_ending=False
            mode="SYSTEMS"
            snd(LOCK)

    elif a.startswith("ENGPART:"):
        n=a.split(":",1)[1]
        if engineering_data>=5:
            engine_parts[n]=min(100,engine_parts[n]+20)
            engineering_data-=5
            snd(CLICK)
        else:
            log("INSUFFICIENT ENGINEERING DATA.")
            snd(WARN_S)

    elif a.startswith("REROUTE:"):
        n=a.split(":",1)[1]

        # Recovery puzzle:
        # Only surplus readiness above the 60% viable threshold can be cannibalised.
        # -10% readiness returns +3 Engineering Data.
        if engine_parts[n] > 60:
            engine_parts[n]=max(60,engine_parts[n]-10)
            engineering_data+=3
            log(f"REROUTED {n} // -10% READINESS // +3 ENG")
            snd(CLICK)
        else:
            log(f"{n} AT MINIMUM VIABLE READINESS // CANNOT REROUTE")
            snd(WARN_S)

    elif a=="BUILD_ENGINE":
        engine_built=all(v>=60 for v in engine_parts.values())
        if engine_built:
            record("ANGEL ENGINE ASSEMBLED AROUND LOCAL HOST.")
            snd(ENGINE)
        else:
            log("ENGINE ASSEMBLY INCOMPLETE // modules require 60% minimum.")
            snd(WARN_S)

    elif a.startswith("OUTPUT:"):
        engine_output=int(a.split(":")[1])
        snd(CLICK)

    elif a=="DRAW_ENGINE" and engine_built:
        engine_draws+=1
        record(f"ENGINE DRAW // OUTPUT {engine_output}%")
        snd(ENGINE)
        if engine_output>=55:
            # Deliberately reuse the aversive signature established in Host Observation.
            snd(HOST_PAIN)
            log("HOST RESPONSE SIGNATURE // MATCH FOUND")
            record("Engine extraction reproduced previously observed aversive response signature.")

    elif a.startswith("MIRACLE:") and engine_built:
        target=a.split(":",1)[1]
        miracles_done.add(target)
        record(f"ANOMALOUS INTERVENTION // {target} // SUCCESS")
        snd(MIRACLE)
        if len(miracles_done)>=3:
            human_restoring=True
            record("HUMAN STABILISATION DEPLOYMENT AUTHORISED.")

    elif a=="PROFIT" and final_choice:
        final_choice=False
        ending_route="PROFIT"
        ending_timer=0.
        log("FINAL SELECTION // PROFIT")
        snd(CASH)
        return

    elif a=="RELEASE" and final_choice:
        final_choice=False
        ending_route="RELEASE"
        ending_timer=0.
        log("FINAL SELECTION // RELEASE ME")
        snd(LOW)
        return

    elif a=="BEGIN_RECEPTION":
        reception_active=True;mode="RECEPTION";snd(LOW)

def startscreen():
    # Title screen only: pure black field, radiant white Phenomenon.
    screen.fill((0,0,0))

    cx=W//2
    cy=int(H*.46)
    tm=pygame.time.get_ticks()/1000.0

    # Very subtle breathing only.
    pulse=1.0 + math.sin(tm*1.35)*.018

    if title_transition:
        p=max(0.0,min(1.0,title_transition_t/title_transition_duration))
        eased=1-(1-p)**3
        core_r=sc(28 + 1020*eased)
        bloom_r=sc(220 + 1500*eased)
        spike_gain=1.0 + 4.2*eased
    else:
        # Slightly larger visual presence than 0.7.6.2.
        core_r=sc(32*pulse)
        bloom_r=sc(270*pulse)
        spike_gain=1.28

    surf=pygame.Surface((W,H),pygame.SRCALPHA)

    # ------------------------------------------------------------------
    # PURE WHITE BLOOM
    # No grey rings, no specks, no visible circular bands.
    # ------------------------------------------------------------------
    glow_layers=38
    for i in range(glow_layers,0,-1):
        frac=i/glow_layers
        r=max(1,int(bloom_r*frac))
        alpha=max(1,int((1-frac)**1.8*34))
        pygame.draw.circle(surf,(255,255,255,alpha),(cx,cy),r)

    # Additional soft inner bloom, still pure white.
    for r_mult,alpha in [
        (3.25,16),
        (2.80,22),
        (2.35,30),
        (1.95,42),
        (1.60,62),
        (1.30,92),
    ]:
        rr=max(sc(1),int(core_r*r_mult))
        pygame.draw.circle(surf,(255,255,255,alpha),(cx,cy),rr)

    # ------------------------------------------------------------------
    # FADING WHITE SPIKES
    # ------------------------------------------------------------------
    ray_count=72
    for i in range(ray_count):
        base=(i/ray_count)*math.pi*2
        ang=base + math.sin(i*1.731)*.055 + math.sin(tm*.28+i*.37)*.012

        length=sc(82 + (i*37)%150)
        if i%9==0:
            length=int(length*1.60)
        elif i%5==0:
            length=int(length*1.26)
        length=int(length*spike_gain)

        start_r=max(sc(8),int(core_r*.72))
        segments=20

        for s in range(segments):
            a=s/segments
            b=(s+1)/segments
            seg_start=start_r + length*a
            seg_end=start_r + length*b
            alpha=int(125*(1-a)**2.2)
            width=max(1,sc(5 - int(a*4)))

            x1=cx+math.cos(ang)*seg_start
            y1=cy+math.sin(ang)*seg_start
            x2=cx+math.cos(ang)*seg_end
            y2=cy+math.sin(ang)*seg_end

            pygame.draw.line(
                surf,
                (255,255,255,max(1,alpha)),
                (x1,y1),
                (x2,y2),
                width
            )

        if i%2==0:
            ang2=ang + .012*(1 if i%4==0 else -1)
            length2=int(length*.82)
            segments2=15

            for s in range(segments2):
                a=s/segments2
                b=(s+1)/segments2
                seg_start=start_r + length2*a
                seg_end=start_r + length2*b
                alpha=int(50*(1-a)**2.0)

                x1=cx+math.cos(ang2)*seg_start
                y1=cy+math.sin(ang2)*seg_start
                x2=cx+math.cos(ang2)*seg_end
                y2=cy+math.sin(ang2)*seg_end

                pygame.draw.line(
                    surf,
                    (255,255,255,max(1,alpha)),
                    (x1,y1),
                    (x2,y2),
                    1
                )

    # Blown-out white centre with no internal detail.
    pygame.draw.circle(surf,(255,255,255,160),(cx,cy),max(sc(1),int(core_r*2.15)))
    pygame.draw.circle(surf,(255,255,255,215),(cx,cy),max(sc(1),int(core_r*1.52)))
    pygame.draw.circle(surf,(255,255,255,255),(cx,cy),core_r)

    # Touch transition: same white source expands to engulf the display.
    if title_transition:
        p=max(0.0,min(1.0,title_transition_t/title_transition_duration))
        white_alpha=int(255*max(0,(p-.36)/.64))
        if white_alpha>0:
            wash=pygame.Surface((W,H),pygame.SRCALPHA)
            wash.fill((255,255,255,white_alpha))
            surf.blit(wash,(0,0))

    screen.blit(surf,(0,0))

    # Reposition only the title-screen text to form one centered composition.
    if not title_transition or title_transition_t<title_transition_duration*.42:
        title_y=max(sc(80), cy-bloom_r-sc(155))
        t=HUGE.render("RECEIVER",True,WHITE)
        screen.blit(t,(W/2-t.get_width()/2,title_y))

        prompt_y=min(H-sc(220), cy+bloom_r+sc(55))

        w=FONT.render("WELCOME, DR. ERNSTMANN.",True,WHITE)
        screen.blit(w,(W/2-w.get_width()/2,prompt_y))

        q=SMALL.render("TOUCH ANYWHERE TO BEGIN.",True,TXT)
        screen.blit(q,(W/2-q.get_width()/2,prompt_y+sc(56)))

def home():
    title("RECEIVER FACILITY","Operational research interface",False)

    third=("SYNCHRONISATION","SYNC",True) if hidden_stage>=4 else ("OBSERVATION","OBS",True)
    items=[
      ("SIGNAL MONITOR","SIGNAL",True),
      ("SUBSTRATE LAB","SUBSTRATE",hidden_stage<4),
      third,
      ("ARCHIVE","ARCHIVE",True),
      ("VESSEL LAB","VESSEL",vessel_auth),
      ("ENVIRONMENT","ENV",True)
    ]

    m=sc(28); g=sc(16); y0=sc(130)
    cw=(W-2*m-g)//2; ch=sc(205)

    for i,(name,action,en) in enumerate(items):
        x=m+(i%2)*(cw+g)
        y=y0+(i//2)*(ch+g)
        r=pygame.Rect(x,y,cw,ch)

        # Only the room name is displayed inside each tile.
        buttons.append((r,action,en))
        pygame.draw.rect(screen,PANEL2 if en else PANEL,r,border_radius=sc(16))
        pygame.draw.rect(screen,WHITE if en else DIM,r,sc(2),border_radius=sc(16))

        label=FONT.render(name,True,WHITE if en else DIM)
        screen.blit(label,(r.centerx-label.get_width()/2,r.centery-label.get_height()/2))

        if name=="VESSEL LAB" and not en:
            sealed=SMALL.render("SEALED",True,BAD)
            screen.blit(sealed,(r.centerx-sealed.get_width()/2,r.centery+sc(38)))

    y=y0+3*(ch+g)+sc(18)

    if hidden_stage==1:
        status="CONTAINMENT // NOMINAL"
    elif hidden_stage==2:
        status="REGIONAL ECOLOGY // CRITICAL"
    elif hidden_stage==3:
        status="HUMAN SYSTEMS // DESTABILISING"
    else:
        status="GLOBAL COMMUNICATION // DESYNCHRONISED"

    screen.blit(FONT.render(status,True,WARN),(m,y))
    y+=sc(48)
    screen.blit(SMALL.render(logs[-1],True,TXT),(m,y))

    # Only ONE progression button is ever added beneath the six original room tiles.
    # This prevents late-game controls being pushed off the bottom of a phone screen.
    action_y=min(y+sc(70), H-sc(155))

    if host_unlocked:
        button((m,action_y,W-2*m,sc(78)),
               "ADVANCED SYSTEMS",
               "SYSTEMS",True,True,FONT)
    elif sync_locked:
        button((m,action_y,W-2*m,sc(78)),
               "CONNECTION STABLE // OPEN RECEPTION",
               "RECEPTION",True,True,FONT)

def systems():
    title("ADVANCED SYSTEMS","Late-stage host and engine controls")
    y=sc(165)
    gap=sc(24)
    bh=sc(118)

    items=[
        ("HOST OBSERVATION","HOST",host_unlocked),
        ("APPLICATIONS","APPLICATIONS",applications_unlocked),
        ("ANGEL ENGINE","ENGINE",engine_unlocked)
    ]

    for label,action,en in items:
        button((sc(32),y,W-sc(64),bh),label,action,en,en,FONT)
        y+=bh+gap

    y+=sc(30)
    if engine_unlocked:
        para("ANGEL ENGINE AUTHORISED // CONSTRUCTION ACCESS AVAILABLE.",
             sc(32),y,W-sc(64),WARN,FONT)
    elif applications_unlocked:
        remaining=max(0,3-applications_done)
        para(f"Applications testing active // {remaining} unique intervention(s) remain.",
             sc(32),y,W-sc(64),TXT,SMALL)
    elif host_unlocked:
        para("Local host observation active.",sc(32),y,W-sc(64),TXT,SMALL)

def signal():
    title("SIGNAL MONITOR","Tap segments to tune.")

    y=sc(140)
    for name,val,key in [
        ("FREQUENCY",freq,"FREQ"),
        ("PHASE",phase,"PHASE"),
        ("STRENGTH",strength,"STRENGTH")
    ]:
        screen.blit(FONT.render(f"{name}: {val:03d}",True,TXT),(sc(30),y))
        bar=pygame.Rect(sc(30),y+sc(48),W-sc(60),sc(64))
        pygame.draw.rect(screen,PANEL2,bar,border_radius=sc(10))
        pygame.draw.rect(screen,DIM,bar,sc(2),border_radius=sc(10))

        sw=bar.w//10
        for i in range(10):
            rr=pygame.Rect(bar.x+i*sw,bar.y,sw,bar.h)
            buttons.append((rr,f"{key}:{(i+1)*10}",True))
            if (i+1)*10<=val:
                pygame.draw.rect(screen,(42,65,63),
                                 rr.inflate(-sc(5),-sc(8)),
                                 border_radius=sc(6))
        y+=sc(160)

    c=compat(subs[selected])
    screen.blit(BIG.render(f"COHERENCE {int(c*100):02d}%",True,WARN),(sc(30),y))

    # Animated live waveform. Poor alignment = noisy/weak;
    # high coherence = stronger and more ordered.
    graph=pygame.Rect(sc(30),y+sc(80),W-sc(60),sc(330))
    pygame.draw.rect(screen,PANEL,graph,border_radius=sc(12))
    pygame.draw.rect(screen,DIM,graph,sc(2),border_radius=sc(12))

    mid=graph.centery
    pygame.draw.line(screen,(45,58,57),(graph.left,mid),(graph.right,mid),sc(1))

    tm=pygame.time.get_ticks()/1000.0
    pts=[]
    amp=sc(15 + 95*c) * (0.45 + strength/180)
    noise_amp=sc(28*(1-c)+3)
    phase_shift=(phase/100.0)*math.pi*2
    cycles=2.0 + freq/17.0

    for px in range(graph.left+sc(5),graph.right-sc(5),3):
        xn=(px-graph.left)/max(1,graph.w)
        ordered=math.sin(xn*math.pi*2*cycles + tm*3.0 + phase_shift)
        harmonic=math.sin(xn*math.pi*2*(cycles*.5)+tm*1.2)*(.22*c)
        noise=random.uniform(-1,1)*noise_amp
        yy=mid + (ordered+harmonic)*amp + noise
        yy=max(graph.top+sc(8),min(graph.bottom-sc(8),yy))
        pts.append((px,int(yy)))

    if len(pts)>1:
        pygame.draw.lines(screen,TXT,False,pts,sc(2))

    screen.blit(SMALL.render("LIVE CONTACT WAVEFORM",True,DIM),
                (graph.x+sc(14),graph.y+sc(12)))

def substrate():
    title("SUBSTRATE LAB","Long exposure may propagate beyond containment.")

    y=sc(132)
    h=sc(96)

    for i,n in enumerate(subs):
        ok=available(n)
        r=pygame.Rect(sc(26),y+i*(h+sc(11)),W-sc(52),h)
        button(r,n if ok else n+" [LOCKED]",f"SUB:{n}",ok,n==selected,FONT)

    y += 4*(h+sc(11))+sc(14)
    c=compat(subs[selected])

    screen.blit(FONT.render(
        f"COHERENCE {int(c*100):02d}%  TIME {etime:04.1f}s  DATA {knowledge}",
        True,TXT),(sc(26),y))

    y+=sc(54)

    # Primary experiment action is deliberately high on the screen,
    # directly beneath the experiment statistics.
    button((sc(26),y,W-sc(52),sc(84)),
           "STOP EXPOSURE" if experiment else "START EXPOSURE",
           "EXPOSE",True,True,FONT)

    y+=sc(105)

    if experiment:
        screen.blit(BIG.render(
            "EXPOSURE ACTIVE",
            True,
            BAD if etime>=25 else WARN),(sc(26),y))

        y+=sc(58)

        if etime>=25:
            para("CONTAINMENT WARNING // propagation accelerating.",
                 sc(26),y,W-sc(52),BAD,FONT)
        elif etime>=15:
            para("CONTACT ACTIVITY INCREASING // static accumulation detected.",
                 sc(26),y,W-sc(52),WARN,FONT)

    elif post_persist>0:
        screen.blit(BIG.render(
            "SIGNAL OFF // PATTERN REMAINS",
            True,WHITE),(sc(26),y))

def archive():
    title("ARCHIVE","Persistent verified findings")
    y=sc(130)
    if not records:para("No verified findings.",sc(26),y,W-sc(52),DIM,FONT)
    for i,r in enumerate(records[-13:],1):
        y=para(f"{i:02d} // {r}",sc(26),y,W-sc(52),TXT,SMALL)+sc(9)
        if y>H-sc(60):break

def env():
    title("ENVIRONMENTAL MONITOR","External conditions")
    y=sc(180)
    screen.blit(BIG.render(f"WILDLIFE INDEX   {wildlife:05.1f}%",True,WHITE if wildlife>20 else BAD),(sc(30),y));y+=sc(100)
    screen.blit(BIG.render(f"HUMAN STABILITY  {human:05.1f}%",True,WHITE if human>30 else BAD),(sc(30),y));y+=sc(125)
    if wildlife<=0:y=para("BIOLOGICAL ACTIVITY: NOT DETECTED. Propagation continues.",sc(30),y,W-sc(60),BAD,FONT)
    elif wildlife<70:y=para("Regional ecological collapse is accelerating.",sc(30),y,W-sc(60),WARN,FONT)
    if hidden_stage>=3:y=para("Communications, behaviour and infrastructure are losing coherent organisation.",sc(30),y+sc(25),W-sc(60),BAD,FONT)
    if hidden_stage>=4:para("ORDER: LOST // NETWORK SYNCHRONY: RISING.",sc(30),y+sc(25),W-sc(60),WHITE,BIG)

def obs():
    title("OBSERVATION / CCTV","Image boundary integrity monitor")
    f=pygame.Rect(sc(28),sc(130),W-sc(56),H-sc(205));pygame.draw.rect(screen,(3,5,6),f);pygame.draw.rect(screen,DIM,f,sc(3))
    screen.blit(SMALL.render("CAM 03 // LIVE",True,TXT),(f.x+sc(14),f.y+sc(14)))
    if anomaly>.25:
        cx=f.centerx;cy=f.centery;pygame.draw.circle(screen,DIM,(cx,cy-sc(70)),sc(35),sc(3))
        pygame.draw.line(screen,DIM,(cx,cy-sc(35)),(cx,cy+sc(100)),sc(4))
        pygame.draw.line(screen,DIM,(cx,cy),(cx-sc(80),cy+sc(55)),sc(4))
        end=min(W-sc(4),f.right+int(max(0,anomaly-.45)*sc(330)));pygame.draw.line(screen,WHITE,(cx,cy),(end,cy-sc(25)),sc(6))
        if anomaly>.52:screen.blit(SMALL.render("FRAME BOUNDARY VIOLATION",True,WARN),(f.x+sc(14),f.bottom-sc(45)))
    else:
        t=FONT.render("NO ANOMALIES",True,DIM);screen.blit(t,(f.centerx-t.get_width()/2,f.centery))

def vessel():
    title("VESSEL LAB","Mechanical host construction")
    y=sc(130)
    para("Construct a physical receiver using the properties isolated from earlier substrate tests.",sc(26),y,W-sc(52),TXT,SMALL);y+=sc(75)
    for n in vessel_parts:
        button((sc(26),y,W-sc(52),sc(88)),f"{n:10} {vessel_parts[n]:03d}%   +10 / 5 DATA",f"PART:{n}",knowledge>=5,False,FONT);y+=sc(102)
    screen.blit(FONT.render(f"AVAILABLE DATA: {knowledge}",True,WARN),(sc(26),y));y+=sc(52)
    button((sc(26),y,W-sc(52),sc(76)),"ASSEMBLE / UPDATE PHYSICAL HOST","ASSEMBLE",True,True,FONT);y+=sc(94)
    if vessel_built:
        c=compat(vt());bal=min(vt());col=WHITE if vessel_viable else WARN
        screen.blit(FONT.render(f"COHERENCE {int(c*100):02d}%  BALANCE {int(bal*100):02d}%",True,col),(sc(26),y));y+=sc(48)
        screen.blit(FONT.render("HOST STATUS: "+("VIABLE" if vessel_viable else "INCOMPLETE"),True,col),(sc(26),y));y+=sc(58)
        button((sc(26),y,W-sc(52),sc(74)),"ROUTE TEST CONTACT INTO HOST","HOSTTEST",True,True,FONT)

def syncscreen():
    title("PRAY. PRAY. PRAY.","Alignment / connection array")
    y=sc(140);score=sync_score()
    screen.blit(BIG.render(f"NETWORK ALIGNMENT {int(score):02d}%",True,WHITE if score>=90 else WARN),(sc(28),y));y+=sc(82)
    for idx,val in enumerate(sync):
        screen.blit(FONT.render(f"CHANNEL {idx+1} // PHASE {val:03d}",True,TXT),(sc(28),y))
        bar=pygame.Rect(sc(28),y+sc(45),W-sc(56),sc(68));pygame.draw.rect(screen,PANEL2,bar,border_radius=sc(10));sw=bar.w//10
        for i in range(10):
            rr=pygame.Rect(bar.x+i*sw,bar.y,sw,bar.h);button(rr,"",f"SYNC:{idx}:{(i+1)*10}")
            if (i+1)*10<=val:pygame.draw.rect(screen,(42,65,63),rr.inflate(-sc(5),-sc(8)),border_radius=sc(6))
        y+=sc(160)
    if not vessel_viable:para("Alignment can be attempted, but no viable receiving vessel is available.",sc(28),y,W-sc(56),BAD,FONT)
    elif sync_locked:
        para("CHANNELS LOCKED // CONNECTION COHERENT // RECEIVER AVAILABLE",sc(28),y,W-sc(56),WHITE,FONT)
        button((sc(28),y+sc(80),W-sc(56),sc(80)),"ROUTE CONNECTION TO VESSEL","RECEPTION",True,True,FONT)
    else:para("Bring unstable channels into phase. A viable physical host must be waiting before reception.",sc(28),y,W-sc(56),TXT,FONT)

def reception_screen():
    title("RECEPTION CONTROL","Viable physical host connected")
    remote=max(0,100-reception);local=min(100,reception)
    y=sc(175)
    screen.blit(BIG.render(f"REMOTE COHERENCE   {int(remote):03d}%",True,TXT),(sc(30),y));y+=sc(95)
    screen.blit(BIG.render(f"VESSEL ACTIVITY    {int(local):03d}%",True,WHITE if local>50 else WARN),(sc(30),y));y+=sc(115)
    # transfer bars
    for label,val in [("REMOTE",remote),("VESSEL",local)]:
        screen.blit(FONT.render(label,True,DIM),(sc(30),y))
        r=pygame.Rect(sc(210),y,W-sc(250),sc(44));pygame.draw.rect(screen,PANEL2,r,border_radius=sc(8))
        pygame.draw.rect(screen,TXT,(r.x,r.y,int(r.w*val/100),r.h),border_radius=sc(8));y+=sc(75)
    if not reception_active and not reception_done:
        para("Connection is coherent. Route the incoming pattern into the prepared vessel.",sc(30),y+sc(20),W-sc(60),TXT,FONT)
        button((sc(30),y+sc(110),W-sc(60),sc(82)),"BEGIN RECEPTION","BEGIN_RECEPTION",True,True,FONT)
    elif reception_active:
        para("TRANSFER ACTIVE // maintain connection.",sc(30),y+sc(20),W-sc(60),WARN,FONT)
    elif reception_done:
        screen.blit(BIG.render("EXTERNAL SIGNAL: NONE",True,DIM),(sc(30),y+sc(20)))
        screen.blit(BIG.render("VESSEL ACTIVITY: PERSISTENT",True,WHITE),(sc(30),y+sc(85)))
        screen.blit(FONT.render("SOURCE: LOCAL",True,WARN),(sc(30),y+sc(155)))
        if agency_stage>=1:para("Diagnostic request transmitted: IDENTIFY.",sc(30),y+sc(220),W-sc(60),TXT,FONT)
        if agency_stage>=2:para("NO RESPONSE.",sc(30),y+sc(275),W-sc(60),DIM,FONT)
        if agency_stage>=3:para("ARCHIVE ACCESS DETECTED // no operator command issued.",sc(30),y+sc(330),W-sc(60),WARN,FONT)
        if agency_stage>=4:para("NEW ARCHIVE ENTRY:  I AM HERE.",sc(30),y+sc(390),W-sc(60),WHITE,BIG)

def hostscreen():
    title("HOST OBSERVATION","Local vessel activity / stimulus-response study")
    y=sc(132)

    screen.blit(FONT.render("VESSEL STATUS: ACTIVE",True,WHITE),(sc(28),y))
    y+=sc(48)
    screen.blit(FONT.render(f"RESPONSE INDEX: {int(host_response):03d}",True,WARN),(sc(28),y))
    y+=sc(70)

    graph=pygame.Rect(sc(28),y,W-sc(56),sc(245))
    pygame.draw.rect(screen,PANEL,graph,border_radius=sc(12))
    pygame.draw.rect(screen,DIM,graph,sc(2),border_radius=sc(12))
    mid=graph.centery
    pts=[]; tm=pygame.time.get_ticks()/1000.
    amp=sc(14+host_response*.45)
    for px in range(graph.left+sc(5),graph.right-sc(5),3):
        xn=(px-graph.left)/max(1,graph.w)
        yy=mid+math.sin(xn*math.pi*12+tm*2.4)*amp
        yy+=math.sin(xn*math.pi*31+tm*.8)*sc(5)
        pts.append((px,int(yy)))
    if len(pts)>1:pygame.draw.lines(screen,TXT,False,pts,sc(2))
    screen.blit(SMALL.render("LOCAL ACTIVITY",True,DIM),(graph.x+sc(12),graph.y+sc(10)))

    y=graph.bottom+sc(28)
    para("Apply controlled stimuli and register the response. No direct communication protocol is assumed.",sc(28),y,W-sc(56),TXT,SMALL)
    y+=sc(82)

    labels=[
        ("VISUAL INFORMATION","HOSTSTIM:VISUAL"),
        ("AUDIO / SIGNAL","HOSTSTIM:AUDIO"),
        ("MECHANICAL STIMULUS","HOSTSTIM:MECHANICAL"),
        ("ELECTRICAL STIMULUS","HOSTSTIM:ELECTRICAL")
    ]
    for label,action in labels:
        button((sc(28),y,W-sc(56),sc(72)),label,action,True,False,FONT)
        y+=sc(84)

    if host_comm_stage>=1:
        para("AVERSIVE RESPONSE: REPEATABLE",sc(28),y+sc(8),W-sc(56),BAD,FONT)
    if host_comm_stage>=2:
        para("STRUCTURED RESPONSE PROTOCOL: ACTIVE",sc(28),y+sc(58),W-sc(56),WHITE,FONT)
    if host_comm_stage>=3:
        para("UNSOLICITED STRUCTURED OUTPUT DETECTED",sc(28),y+sc(108),W-sc(56),WARN,FONT)

    if facility_failure and not host_helped:
        para("FACILITY POWER REGULATION FAILURE // HOST ACTIVITY CHANGED WITHOUT STIMULUS.",sc(28),y+sc(165),W-sc(56),BAD,SMALL)
        button((sc(28),y+sc(235),W-sc(56),sc(76)),"ALLOW HOST NETWORK ACCESS","HOST_HELP",True,True,FONT)

def applications():
    title("APPLICATIONS","Controlled host-assisted interventions")
    y=sc(145)
    para("The local host has demonstrated voluntary corrective action. Route damaged systems for controlled assistance.",sc(28),y,W-sc(56),TXT,FONT)
    y+=sc(135)

    targets=[
        ("COMMUNICATION RELAY","COMMUNICATION RELAY"),
        ("POWER REGULATION","POWER REGULATION"),
        ("DATA RECOVERY","DATA RECOVERY")
    ]
    for label,target in targets:
        done=target in applications_completed
        button((sc(28),y,W-sc(56),sc(88)),
               label+(" // COMPLETE" if done else ""),
               f"APP:{target}",
               not done,
               not done,
               FONT)
        y+=sc(108)

    screen.blit(FONT.render(f"SUCCESSFUL INTERVENTIONS: {applications_done}/3",True,WARN),(sc(28),y))
    y+=sc(55)
    screen.blit(SMALL.render(f"ENGINEERING DATA: {engineering_data}",True,TXT),(sc(28),y))
    y+=sc(65)

    if project_revealed:
        screen.blit(BIG.render("NEW PROJECT AUTHORISATION",True,WHITE),(sc(28),y))
        y+=sc(75)
        screen.blit(FONT.render("HOST INTEGRATION PROGRAM",True,TXT),(sc(28),y))
        y+=sc(70)
        screen.blit(HUGE.render("ANGEL ENGINE",True,WARN),(sc(28),y))


def enginescreen():
    title("ANGEL ENGINE","Host integration / anomalous intervention system")
    y=sc(128)

    if not engine_built:
        para("Construct an integration system around the existing local host. Minimum module readiness: 60%.",sc(28),y,W-sc(56),TXT,SMALL)
        y+=sc(82)

        # Compact one-row-per-module layout so every control remains visible on mobile.
        for n in engine_parts:
            row=pygame.Rect(sc(28),y,W-sc(56),sc(82))
            pygame.draw.rect(screen,PANEL2,row,border_radius=sc(12))
            pygame.draw.rect(screen,DIM,row,sc(2),border_radius=sc(12))

            # Upgrade area: left ~72% of the row.
            up_w=int(row.w*.72)
            up=pygame.Rect(row.x,row.y,up_w,row.h)
            buttons.append((up,f"ENGPART:{n}",engineering_data>=5))
            label=FONT.render(f"{n:10} {engine_parts[n]:03d}%   +20 / 5 ENG",
                              True,WHITE if engineering_data>=5 else DIM)
            screen.blit(label,(up.x+sc(14),up.centery-label.get_height()/2))

            # Reroute area: compact button on the right.
            rr=pygame.Rect(row.x+up_w+sc(8),row.y+sc(10),row.w-up_w-sc(18),row.h-sc(20))
            can_reroute=engine_parts[n] > 60
            buttons.append((rr,f"REROUTE:{n}",can_reroute))
            pygame.draw.rect(screen,PANEL if not can_reroute else PANEL2,rr,border_radius=sc(9))
            pygame.draw.rect(screen,DIM if not can_reroute else WHITE,rr,sc(2),border_radius=sc(9))
            rt=SMALL.render("REROUTE" if can_reroute else "LOCKED",
                            True,WHITE if can_reroute else DIM)
            screen.blit(rt,(rr.centerx-rt.get_width()/2,rr.centery-rt.get_height()/2))

            y+=sc(94)

        # Keep resources and assembly safely above Android navigation area.
        screen.blit(FONT.render(f"ENGINEERING DATA: {engineering_data}",True,WARN),(sc(28),y))
        y+=sc(50)

        para("Reroute removes 10% surplus readiness and returns 3 ENG. Modules cannot be reduced below 60%.",
             sc(28),y,W-sc(56),DIM,SMALL)
        y+=sc(66)

        ready=all(v>=60 for v in engine_parts.values())
        assemble_y=min(y, H-sc(150))
        button((sc(28),assemble_y,W-sc(56),sc(78)),
               "ASSEMBLE ANGEL ENGINE" if ready else "ALL MODULES MUST REACH 60%",
               "BUILD_ENGINE",
               ready,
               ready,
               FONT if ready else SMALL)
        return

    screen.blit(FONT.render(f"ENGINE OUTPUT: {engine_output:03d}%",True,WHITE),(sc(28),y))
    y+=sc(52)
    para("Output controls extraction intensity. Host activity is monitored continuously.",sc(28),y,W-sc(56),TXT,SMALL)
    y+=sc(70)

    # Touch-first output choices.
    vals=[20,40,60,80,100]
    gap=sc(8); bw=(W-sc(56)-gap*4)//5
    for i,v in enumerate(vals):
        button((sc(28)+i*(bw+gap),y,bw,sc(68)),str(v),f"OUTPUT:{v}",True,v==engine_output,SMALL)
    y+=sc(85)
    button((sc(28),y,W-sc(56),sc(78)),"DRAW FROM ENGINE","DRAW_ENGINE",True,True,FONT)
    y+=sc(105)

    if len(miracles_done)<3:
        para("ROUTING TARGETS",sc(28),y,W-sc(56),WARN,FONT);y+=sc(48)
        for label,key in [
            ("RESTORE COMMUNICATION NETWORK","COMMUNICATION"),
            ("STABILISE POWER INFRASTRUCTURE","POWER"),
            ("CORRECT HUMAN SYSTEM INSTABILITY","HUMAN SYSTEMS")]:
            done=key in miracles_done
            button((sc(28),y,W-sc(56),sc(74)),
                   label+(" // COMPLETE" if done else ""),
                   f"MIRACLE:{key}",not done,not done,SMALL)
            y+=sc(86)
    elif human<99.9:
        para("HUMAN STABILISATION ACTIVE",sc(28),y,W-sc(56),WHITE,BIG)
        y+=sc(70)
        screen.blit(FONT.render(f"HUMAN STABILITY {human:05.1f}%",True,WARN),(sc(28),y))
        y+=sc(55)
        screen.blit(FONT.render("WILDLIFE INDEX   000.0%",True,DIM),(sc(28),y))
    else:
        para("HUMAN SYSTEMS: STABLE",sc(28),y,W-sc(56),WHITE,BIG)
        y+=sc(70)
        screen.blit(FONT.render("HUMAN STABILITY 100.0%",True,WHITE),(sc(28),y))
        y+=sc(55)
        screen.blit(FONT.render("WILDLIFE INDEX   000.0%",True,DIM),(sc(28),y))
        y+=sc(70)
        para("The host remains integrated with the systems now maintaining human stability.",
             sc(28),y,W-sc(56),WARN,SMALL)

def finalchoice():
    title("HUMAN STABILISATION","Host integration maintaining recovered systems",False)
    y=sc(165)

    screen.blit(BIG.render("HUMAN STABILITY 100.0%",True,WHITE),(sc(28),y));y+=sc(82)
    screen.blit(BIG.render("WILDLIFE INDEX   000.0%",True,DIM),(sc(28),y));y+=sc(112)

    para("HOST OUTPUT: STABLE",sc(28),y,W-sc(56),DIM,FONT);y+=sc(62)
    para("UNSOLICITED HOST MESSAGE:",sc(28),y,W-sc(56),WARN,FONT);y+=sc(54)
    screen.blit(HUGE.render("RELEASE ME.",True,WHITE),(sc(28),y))

    # Large, non-overlapping touchscreen choices.
    # PROFIT occupies the upper choice region.
    profit_y=sc(625)
    release_y=sc(805)

    button((sc(28),profit_y,W-sc(56),sc(118)),
           "PROFIT","PROFIT",True,True,HUGE)

    button((sc(110),release_y,W-sc(220),sc(84)),
           "RELEASE ME","RELEASE",True,False,FONT)

def draw_credits():
    screen.fill(BG)
    t=credits_timer

    if t<3:
        msg="TRANSMISSION TERMINATED" if str(ending_route).startswith("RELEASE") else "PROTOCOL COMPLETE."
        r=BIG.render(msg,True,DIM)
        screen.blit(r,(W/2-r.get_width()/2,H*.38))

    elif t<8:
        r=BIG.render("RECEIVER",True,WHITE)
        screen.blit(r,(W/2-r.get_width()/2,H*.38))

    else:
        r=HUGE.render("RECEIVER",True,WHITE)
        screen.blit(r,(W/2-r.get_width()/2,H*.34))
        q=BIG.render("A Fan Game By DecoySnake",True,TXT)
        screen.blit(q,(W/2-q.get_width()/2,H*.45))

running=True
if TITLE_AMBIENCE:
    try:
        title_channel=TITLE_AMBIENCE.play(loops=-1)
    except pygame.error:
        title_channel=None

while running:
    dt=clock.tick(60)/1000;events=pygame.event.get();buttons.clear()

    # TITLE SCREEN TRANSITION ONLY.
    if mode=="TITLE" and title_transition:
        title_transition_t+=dt
        if title_transition_t>=title_transition_duration:
            mode="HOME"
            title_transition=False
            title_transition_t=0.0

    if mode=="SUBSTRATE" and experiment:
        etime+=dt;p=subs[selected];c=compat(p);anomaly=max(anomaly,c*min(1,etime/25))
        if selected in ("BIOLOGICAL","NEURAL"):
            rate=(.25+strength*.008)*(.65+c)
            if etime>12:rate*=2.0
            if etime>22:rate*=3.0
            wildlife=max(0,wildlife-rate*dt)
        elif etime>25:wildlife=max(0,wildlife-.025*strength*dt)
        if etime>=22:
            # Red = facility/containment danger. Pulses become more insistent with time.
            flash_red=max(flash_red,.24)
            alarm-=dt
            if alarm<=0:
                snd(WARN_S)
                alarm=max(.28,1.15-(etime-22)*.03)

        # White = contact/Phenomenon activity.
        # It can punch through the red during strong or prolonged exposures.
        white_rate=.20
        if c>.35: white_rate += c*.55
        if etime>16: white_rate += .35
        if etime>26: white_rate += .55
        if random.random()<dt*white_rate:
            flash_white=max(flash_white,.11 if c<.5 else .17)
            snd(CONTACT)

        if etime>=45:
            complete_experiment()

    if wildlife<=0 and hidden_stage<3:
        hidden_stage=3;record("Regional wildlife activity has collapsed completely.");record("Human systems destabilising.");snd(WARN_S)
    if hidden_stage==3:
        # Cascading disarray: ~60-75 seconds rather than >2 minutes.
        collapse_rate=1.0 + (100.-human)*.012
        human=max(0,human-dt*collapse_rate)
        anomaly=min(1,anomaly+dt*.003)
        if human<=0:
            hidden_stage=4;record("Human stability has reached zero.");record("PRAY. PRAY. PRAY.");snd(LOCK)

    if reception_active:
        reception=min(100,reception+dt*12)
        if random.random()<dt*1.4:flash_white=.07;snd(CONTACT)
        if reception>=100:
            reception_active=False;reception_done=True;agency_stage=1;agency_timer=0
            record("External carrier absent. Vessel activity persists locally.");snd(LOW)
    if reception_done and not ending:
        agency_timer+=dt
        if agency_stage==1 and agency_timer>2.5:agency_stage=2;snd(BEEP)
        if agency_stage==2 and agency_timer>5.0:agency_stage=3;snd(CONTACT)
        if agency_stage==3 and agency_timer>8.0:
            agency_stage=4;record("I AM HERE.");flash_white=.35;snd(LOCK)
        if agency_stage==4 and agency_timer>12.0:
            ending=False
            host_unlocked=True
            mode="HOME"
            record("HOST OBSERVATION authorised.")
            reception_done=False

    if host_unlocked and not host_helped:
        host_hum_timer-=dt
        if mode=="HOST" and host_hum_timer<=0:
            snd(HOST_HUM)
            host_hum_timer=2.2

        if host_comm_stage>=2 and host_comm_stage<3:
            host_comm_timer+=dt
            if host_comm_timer>5.5:
                host_comm_stage=3
                host_comm_timer=0.
                record("Unsolicited structured output detected with no operator stimulus.")
                snd(HOST_REPLY)

        if host_comm_stage>=3 and not facility_failure:
            host_comm_timer+=dt
            if host_comm_timer>6.5:
                facility_failure=True
                facility_integrity=38.
                record("Facility power regulation failure detected.")
                log("POWER REGULATION // CRITICAL")
                snd(WARN_S)

    if human_restoring and human<100 and ending_route is None:
        human=min(100.,human+dt*5.2)
        if random.random()<dt*.35:snd(MIRACLE)
        if human>=100:
            human=100.
            human_restoring=False

            # Final state: humanity is stabilised, wildlife remains extinct.
            wildlife=0.
            final_choice=True
            mode="HOME"
            record("HUMAN STABILITY RESTORED.")
            record("WILDLIFE INDEX REMAINS AT ZERO.")
            record("UNSOLICITED HOST MESSAGE: RELEASE ME.")

    if ending_route=="RELEASE":
        ending_timer+=dt
        # Humanity has made its recovered systems dependent on the Engine.
        human=max(0.,100.-(ending_timer**1.55)*6.5)
        if ending_timer>1.0:
            flash_red=max(flash_red,.18)
        if ending_timer>7.5 or human<=.8:
            credits_active=True
            credits_timer=0.
            ending_route="RELEASE_CREDITS"

    elif ending_route=="PROFIT":
        ending_timer+=dt
        # Leave the protocol reveal on screen long enough to actually read it.
        if ending_timer>8.0:
            credits_active=True
            credits_timer=0.
            ending_route="PROFIT_CREDITS"

    if credits_active:
        credits_timer+=dt
        if credits_timer>14:
            running=False

    post_persist=max(0,post_persist-dt);flash_white=max(0,flash_white-dt);flash_red=max(0,flash_red-dt)

    screen.fill(BG)

    if mode=="TITLE":
        startscreen()

    elif credits_active:
        draw_credits()

    elif ending_route=="RELEASE":
        # Release route: engine drops out and the facility loses coherence.
        jitter=int(min(sc(35),ending_timer*sc(3)))
        screen.blit(BIG.render("HOST INTERFACE: DISCONNECTED",True,DIM),(sc(28)+random.randint(-jitter,jitter),sc(230)))
        screen.blit(BIG.render("ANGEL ENGINE: OFFLINE",True,BAD),(sc(28),sc(330)))
        screen.blit(HUGE.render(f"HUMAN STABILITY {human:05.1f}%",True,BAD),(sc(28),sc(520)))
        screen.blit(BIG.render("WILDLIFE INDEX   000.0%",True,DIM),(sc(28),sc(650)))
        if ending_timer>3:
            for _ in range(int(ending_timer*3)):
                yy=random.randrange(0,H)
                pygame.draw.rect(screen,DIM,(random.randrange(0,W),yy,random.randrange(sc(20),max(sc(21),W//2)),sc(2)))

    elif ending_route=="PROFIT":
        screen.blit(HUGE.render("CONGRATULATIONS.",True,WHITE),(sc(28),sc(260)))
        screen.blit(BIG.render("YOU LEARNED ABSOLUTELY NOTHING.",True,WARN),(sc(28),sc(390)))
        steps=[
          "EXPLOIT YOUR RESOURCES",
          "EXTERMINATE THE WILDLIFE",
          "WATCH YOUR SPECIES FALL INTO DISARRAY",
          "PRAY. PRAY. PRAY.",
          "DIVINE MESSENGER DESCENDS",
          "USE THEIR KINDNESS",
          "SIPHON THEIR ENERGY / PERFORM MIRACLES",
          "RESTORE THE PLANET / PROFIT"]
        y=sc(570)
        for s in steps:
            screen.blit(SMALL.render(s,True,TXT),(sc(35),y));y+=sc(52)

    elif final_choice:
        finalchoice()

    elif build6_ending:
        screen.blit(HUGE.render("HOST INTEGRATION PROGRAM",True,WHITE),(sc(28),sc(300)))
        screen.blit(HUGE.render("ANGEL ENGINE",True,WARN),(sc(28),sc(455)))
        para("The facility has approved a new engineering program based on the local host's demonstrated capabilities.",sc(28),sc(620),W-sc(56),TXT,FONT)
        para("BUILD 0.6 COMPLETE",sc(28),sc(790),W-sc(56),WHITE,BIG)
        button((sc(28),min(sc(900),H-sc(150)),W-sc(56),sc(82)),"END BUILD 0.6","QUIT",True,True,FONT)
    elif mode=="HOME":home()
    elif mode=="SIGNAL":signal()
    elif mode=="SUBSTRATE":substrate()
    elif mode=="ARCHIVE":archive()
    elif mode=="ENV":env()
    elif mode=="OBS":obs()
    elif mode=="VESSEL":vessel()
    elif mode=="SYNC":syncscreen()
    elif mode=="RECEPTION":reception_screen()
    elif mode=="HOST":hostscreen()
    elif mode=="APPLICATIONS":applications()
    elif mode=="ENGINE":enginescreen()
    elif mode=="SYSTEMS":systems()

    if flash_red>0:
        o=pygame.Surface((W,H),pygame.SRCALPHA)
        pulse=.55+.45*math.sin(pygame.time.get_ticks()/85.0)
        alpha=int(70+65*pulse)
        o.fill((205,18,25,alpha))
        screen.blit(o,(0,0))

    if flash_white>0:
        o=pygame.Surface((W,H),pygame.SRCALPHA)
        alpha=165 if flash_white>.10 else 115
        o.fill((255,255,255,alpha))
        screen.blit(o,(0,0))
    pygame.display.flip()

    for e in events:
        if e.type==pygame.QUIT:running=False
        elif e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
            if mode!="TITLE":
                mode="HOME"
        elif e.type in (pygame.MOUSEBUTTONDOWN,pygame.FINGERDOWN):
            if mode=="TITLE":
                if not title_transition:
                    title_transition=True
                    title_transition_t=0.0
                    if title_channel:
                        try:title_channel.fadeout(650)
                        except pygame.error:pass
                    snd(CONTACT)
                continue

            x,y=(int(e.x*W),int(e.y*H)) if e.type==pygame.FINGERDOWN else e.pos
            for r,a,en in reversed(buttons):
                if en and r.collidepoint(x,y):handle(a);break
pygame.quit();sys.exit()
