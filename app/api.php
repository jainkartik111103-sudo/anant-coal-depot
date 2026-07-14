<?php
/* Anant Business sync API — file store, Basic Auth inherited from /app/.htaccess.
   GET  ?pull=1            -> {rev, txns:[...] } (tombstones carry _del:1)
   POST {ops:[{op:'put',t:{...}}|{op:'del',no,u}]} -> {rev} (last-write-wins by u) */
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
$f = __DIR__ . '/data/txns.json';
if (!file_exists($f)) { @mkdir(__DIR__.'/data', 0755, true); file_put_contents($f, json_encode(['rev'=>0,'txns'=>new stdClass()])); }
$h = fopen($f, 'c+'); if (!$h) { http_response_code(500); echo '{"error":"store"}'; exit; }
flock($h, LOCK_EX);
$raw = stream_get_contents($h);
$db = json_decode($raw ?: '{"rev":0,"txns":{}}', true);
if (!isset($db['txns'])) $db = ['rev'=>0,'txns'=>[]];
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  $in = json_decode(file_get_contents('php://input'), true);
  $ops = isset($in['ops']) && is_array($in['ops']) ? $in['ops'] : [];
  foreach ($ops as $op) {
    if (!isset($op['op'])) continue;
    if ($op['op'] === 'put' && isset($op['t']['no'])) {
      $no = $op['t']['no']; $u = isset($op['t']['u']) ? $op['t']['u'] : 0;
      $cur = isset($db['txns'][$no]) ? $db['txns'][$no] : null;
      if (!$cur || (isset($cur['u']) ? $cur['u'] : 0) <= $u) $db['txns'][$no] = $op['t'];
    } elseif ($op['op'] === 'del' && isset($op['no'])) {
      $no = $op['no']; $u = isset($op['u']) ? $op['u'] : 0;
      $cur = isset($db['txns'][$no]) ? $db['txns'][$no] : null;
      if (!$cur || (isset($cur['u']) ? $cur['u'] : 0) <= $u) $db['txns'][$no] = ['no'=>$no,'_del'=>1,'u'=>$u];
    }
  }
  if ($ops) $db['rev']++;
  ftruncate($h, 0); rewind($h); fwrite($h, json_encode($db)); fflush($h);
  flock($h, LOCK_UN); fclose($h);
  echo json_encode(['rev'=>$db['rev']]); exit;
}
flock($h, LOCK_UN); fclose($h);
echo json_encode(['rev'=>$db['rev'], 'txns'=>array_values($db['txns'])]);
