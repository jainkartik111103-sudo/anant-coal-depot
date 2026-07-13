/* Anant Business — shared data layer (db.js). One source of truth: every invoice
   saved here powers register, dashboard, accountant working, reports & reprints.
   Storage: localStorage 'acdb_txns' (array). One invoicing device by rule. */
var ADB = (function(){
  var KEY='acdb_txns';
  function all(){ try{ return JSON.parse(localStorage.getItem(KEY))||[]; }catch(e){ return []; } }
  function saveAll(a){ try{ localStorage.setItem(KEY, JSON.stringify(a)); return true; }catch(e){ return false; } }
  function put(t){ var a=all(); var i=a.findIndex(function(x){return x.no===t.no;}); if(i>=0)a[i]=t; else a.push(t);
    a.sort(function(x,y){ return x.date<y.date?-1:x.date>y.date?1:(x.no<y.no?-1:1); }); return saveAll(a); }
  function get(no){ return all().find(function(x){return x.no===no;})||null; }
  function del(no){ saveAll(all().filter(function(x){return x.no!==no;})); }
  function fmt(n){ return (n||0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2}); }
  var ONES=['','One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten','Eleven','Twelve','Thirteen','Fourteen','Fifteen','Sixteen','Seventeen','Eighteen','Nineteen'];
  var TENS=['','','Twenty','Thirty','Forty','Fifty','Sixty','Seventy','Eighty','Ninety'];
  function two(n){return n<20?ONES[n]:(TENS[Math.floor(n/10)]+(n%10?' '+ONES[n%10]:''));}
  function three(n){var h=Math.floor(n/100),r=n%100;return (h?ONES[h]+' Hundred'+(r?' ':''):'')+(r?two(r):'');}
  function words(n){ if(!n)return 'Zero'; var s='',cr=Math.floor(n/1e7);n%=1e7;var lk=Math.floor(n/1e5);n%=1e5;var th=Math.floor(n/1e3);n%=1e3;
    if(cr)s+=three(cr)+' Crore '; if(lk)s+=three(lk)+' Lakh '; if(th)s+=three(th)+' Thousand '; if(n)s+=three(n); return s.trim(); }
  /* totals from items; sign: credit note = -1 for report aggregation (stored positive) */
  function compute(t){
    var tv=0,g=0,cess=0;
    (t.items||[]).forEach(function(it){ var a=(it.q||0)*(it.r||0); tv+=a; g+=a*(it.g||0)/100; cess+=(it.c||0); });
    var rc=!!t.rc, inAS=t.pos==='AS';
    var cg=(!rc&&inAS)?g/2:0, sg=cg, ig=(!rc&&!inAS)?g:0, rcg=rc?g:0;
    var gt=Math.round(tv+cg+sg+ig+(rc?0:cess));
    return {tv:tv,cg:cg,sg:sg,ig:ig,cess:rc?0:cess,rcGst:rcg,gt:gt};
  }
  function sign(t){ return t.type==='CRN'?-1:1; }
  function b2b(t){ return !!(t.gstin&&t.gstin.length>=15); }
  function inRange(t,f,to){ return (!f||t.date>=f)&&(!to||t.date<=to); }
  function fy(d){ d=d||new Date().toISOString().slice(0,10); var y=+d.slice(0,4),m=+d.slice(5,7); var s=m>=4?y:y-1; return [s+'-04-01',(s+1)+'-03-31']; }
  function month(d){ d=d||new Date().toISOString().slice(0,10); var y=d.slice(0,7); var last=new Date(+d.slice(0,4), +d.slice(5,7), 0).getDate(); return [y+'-01', y+'-'+String(last).padStart(2,'0')]; }
  function quarter(d){ d=d||new Date().toISOString().slice(0,10); var y=+d.slice(0,4),m=+d.slice(5,7);
    var qs=[[4,6],[7,9],[10,12],[1,3]]; var q=m>=4?Math.floor((m-4)/3):3; var a=qs[q];
    var sy=(q===3)?y:y, ey=sy; if(q===3&&m<4){} var s=String(a[0]).padStart(2,'0'), e=String(a[1]).padStart(2,'0');
    var yS=(q===3)?y:y, yE=yS; var lastD=new Date(yE, a[1], 0).getDate();
    return [yS+'-'+s+'-01', yE+'-'+e+'-'+String(lastD).padStart(2,'0')]; }
  function dmy(d){ return d?d.split('-').reverse().join('/'):''; }
  function norm(s){return (s||'').trim().toLowerCase();}
  function customers(){
    var m={};
    all().forEach(function(t){
      var k=norm(t.name)+'|'+(t.phone||'');
      var c=m[k]=m[k]||{name:t.name,phone:t.phone||'',gstin:'',addr:'',pos:t.pos,state:t.state,
        first:t.date,last:t.date,count:0,lifetime:0,out:0,paidN:0,items:null,products:{},vehicles:[],history:[]};
      c.count++; c.last=t.date>c.last?t.date:c.last; c.first=t.date<c.first?t.date:c.first;
      if(t.gstin)c.gstin=t.gstin; if(t.addr)c.addr=t.addr; if(t.phone)c.phone=t.phone;
      c.pos=t.pos;c.state=t.state;
      var sgn=sign(t); c.lifetime+=sgn*t.gt;
      if(t.type!=='CRN'&&!t.paid)c.out+=t.gt; if(t.paid)c.paidN++;
      c.items=t.items; // most recent wins (all() is date-sorted)
      t.items.forEach(function(i){c.products[i.p]={q:i.q,u:i.u,r:i.r};});
      if(t.veh&&c.vehicles.indexOf(t.veh)<0)c.vehicles.unshift(t.veh);
      c.history.unshift({no:t.no,date:t.date,gt:t.gt,paid:t.paid,type:t.type});
    });
    return Object.keys(m).map(function(k){return m[k];})
      .sort(function(a,b){return b.last<a.last?-1:1;});
  }
  function yesterday(){var d=new Date();d.setDate(d.getDate()-1);var s=d.toISOString().slice(0,10);return [s,s];}
  function week(){var d=new Date();var dow=(d.getDay()+6)%7;var s=new Date(d);s.setDate(d.getDate()-dow);
    return [s.toISOString().slice(0,10), d.toISOString().slice(0,10)];}
  function stampBackup(){try{localStorage.setItem('acdb_lastbak',new Date().toISOString().slice(0,10));}catch(e){}}
  function lastBackup(){try{return localStorage.getItem('acdb_lastbak')||'';}catch(e){return '';}}
  return {all:all, put:put, get:get, del:del, customers:customers, yesterday:yesterday, week:week,
          stampBackup:stampBackup, lastBackup:lastBackup, fmt:fmt, words:words, compute:compute,
          sign:sign, b2b:b2b, inRange:inRange, fy:fy, month:month, quarter:quarter, dmy:dmy};
})();
