# Análisis Completo: Octavos de Final (Round of 16) — Copa del Mundo 2026

> [!IMPORTANT]
> Hora del análisis: **4 de Julio 2026, ~7:00 AM ET**. Datos de modelo (traza MCMC) y mercado (Polymarket, `run_pipeline.py odds`, overround ≈ 1.002) capturados en vivo. Cada partido se contrastó con un **segundo modelo independiente (Opta supercomputer)** y las casas de apuestas para triangular. Investigación externa vía la skill `edge-finder`.

## Lectura del bracket en una línea

**Slate muy afilado: 6 PASAR, 2 apuestas modestas.** En seis de ocho partidos, Opta **y** las casas coinciden con el mercado — nuestras divergencias son puntos ciegos conocidos del modelo (subvalora favoritos; no ve calidad individual ni lesiones/altitud/viaje). Las dos únicas oportunidades comparten forma: **Polymarket subvalora el "avanzar" del rival de calidad porque el dinero local infla al anfitrión**, y en ambas un segundo estimador (Opta) queda POR ENCIMA de la línea blanda de Polymarket.

| Partido | Modelo (H/D/A) | Mercado (H/D/A) | Opta / casas | Veredicto |
|---|---|---|---|---|
| Canadá v Marruecos | 32/30/37 | 17/28/54 | Opta MAR 52% ≈ mercado | 🔵 PASAR |
| Paraguay v Francia | 14/25/61 | 4/12/83 | Opta FRA 80% ≈ mercado | 🔵 PASAR |
| Brasil v Noruega | 62/23/15 | 53/26/20 | Opta = mercado; modelo es el outlier | 🔵 PASAR |
| **México v Inglaterra** | 23/26/51 | 30/30/39 | Opta ~66% / casas ~60% **> Polymkt ~56%** | 🟢 **APOSTAR (chico)** |
| Portugal v España | 30/27/44 | 22/26/51 | todos ~50% | 🔵 PASAR |
| **EE.UU. v Bélgica** | 26/25/49 | 33/29/37 | Opta ~57% **> Polymkt ~52%**, pero modelo alto | 🟡 **VIGILAR** |
| Argentina v Egipto | 65/24/11 | 71/20/9 | casas ~84% avanzar ≈ | 🔵 PASAR |
| Suiza v Colombia | 26/27/47 | 27/30/42 | Kalshi ≈ modelo | 🔵 PASAR |

---

## 🟢🟢 4. México vs Inglaterra — 5 de Julio, 8:00 PM ET · Estadio Azteca, CDMX
**`🔥 EDGE GENUINO (triangulado) — APOSTAR CHICO: Inglaterra para Avanzar (solo Polymarket)`**

| Métrica | Modelo | Mercado (Polymarket) | Opta / Casas |
|---|---|---|---|
| 1X2 (90 min) | MEX 23% / Emp 26% / ENG 51% | 30% / 30% / 39% | — |
| **Avanzar ENG** | **66%** | **~56%** | **Opta ~66% · casas ~60%** |
| O2.5 / BTTS | 43% / 46% | — | — |
| Goles proyectados | MEX 0.91 – ENG 1.51 | — | — |

**El caso (por qué NO es solo el modelo):** las casas más líquidas y afiladas (DraftKings, Bet365) ponen a Inglaterra en **~60% para avanzar** y la razón torneo-a-torneo de Opta implica **~66%** — ambas POR ENCIMA del ~56% blando de Polymarket. Clave: **la altitud del Azteca (2,240 m — factor real que nuestro modelo goles-only subestima) YA está en los números afilados**, y aun así quedan por encima de Polymarket. Por lo tanto el hueco es sesgo local/público de Polymarket a favor de México, no información nueva que las casas hayan pasado por alto. Se compra Inglaterra-a-avanzar donde está barato.

**Noticias externas:**
- **Altitud (el gran punto ciego):** Tuchel dijo en público que Inglaterra "no puede adaptarse" (llegaron ~48h antes — zona de peligro). Opta: rendimiento −5-6%, carreras de alta intensidad −3-9% en el Azteca. Esto favorece a México y por eso NO se apuesta Inglaterra-gana-90.
- **México:** localía máxima y real (récord Azteca: 8V-2E en 10 partidos de Mundial, 0 derrotas), plantel completo, 0 goles concedidos en 4 partidos (rivales a 0.56 xG).
- **Inglaterra:** sin RB **Reece James (isquiotibiales, duda mayor)**, Quansah fuera; **Rice** arrastra molestia (esperado apto). Kane en forma récord (13 goles de Mundial).

**Penales:** México **0V-2L** (histórico pésimo). Inglaterra **1V-3L** pero mejorando (Pickford con dossier, plantel de tiradores profundo). Con empate ~26%, un shootout es plausible → inclina a Inglaterra. Refuerza el "avanzar".

**Recomendación:** **APOSTAR CHICO — Inglaterra para Avanzar, mercado de Polymarket** (1 unidad). Modelo 66% / casas ~60% / Opta ~66% vs Polymarket ~56% → edge de +4 a +10pp. **PASAR** Inglaterra-gana-90 (la altitud lo hace improbable en regulación). **Revisar en la alineación (~6:00 PM ET del 5 jul):** si Rice está fuera/limitado, bajar a PASAR.

---

## 🟡 6. Estados Unidos vs Bélgica — 6 de Julio, 8:00 PM ET · Lumen Field, Seattle
**`EDGE CONDICIONAL (degradado) — VIGILAR: Bélgica para Avanzar (mínimo, no todavía)`**

| Métrica | Modelo | Mercado (Polymarket) | Opta / Casas |
|---|---|---|---|
| 1X2 (90 min) | USA 26% / Emp 25% / BEL 49% | 33% / 29% / 37% | — |
| **Avanzar BEL** | **63%** | **~52%** | **Opta ~57-58% · casas ~53%** |
| O2.5 / BTTS | 52% / 54% | — | — |
| Goles proyectados | USA 1.12 – BEL 1.63 | — | — |

**El caso (dos fuerzas opuestas):** misma forma que México-Inglaterra — Polymarket ~52% Bélgica-avanzar es blando vs Opta ~57-58% (76% de los tickets van al USA = sesgo local). PERO **dos banderas rojas achican el edge**: (1) nuestro 63% está inflado — el punto ciego documentado del modelo con Bélgica (le ganó a Senegal 3-2 en la prórroga siendo **superado 1.84 a 3.18 en xG** — está corriendo con suerte, no jugando bien); (2) la localía de EE.UU. **sí es genuina** aquí (Seattle), a diferencia del partido fantasma de Canadá en Houston. Neto justo ~57% vs mercado ~52% ≈ solo +5pp.

**Noticias externas:**
- **EE.UU.:** sin su goleador **Balogun (roja vs Bosnia, suspendido)** — merma real de ataque (lo reemplaza Pepi). Localía real y ruidosa (Lumen Field amplifica el ruido).
- **Bélgica:** plantel completo y sano (De Bruyne, Lukaku, Courtois aptos), pero rendimiento pobre — sobrevivió a Senegal con un penal en el minuto 124.

**Penales:** Courtois es un GK de shootout de élite (Bélgica ganó el shootout de octavos '22 3-0 a España); EE.UU. sin experiencia de shootout mundialista. Ventaja Bélgica — parte de por qué el "avanzar" sigue en VIGILAR.

**Recomendación:** **VIGILAR — no apostar todavía.** Es la MISMA señal "Bélgica-avanzar, modelo>mercado" que casi pierde en octavos (Bélgica 0-2 abajo vs Senegal). Ganan por Courtois y suerte, no por juego. Stake mínimo a lo sumo, solo si Lukaku es titular y la línea se mantiene ≥ actual; PASAR si se ajusta a Bélgica -125. **Nunca** apostar Bélgica-gana-90.

---

## 🔵 1. Canadá vs Marruecos — 4 de Julio, 1:00 PM ET · NRG Stadium, Houston
**`MERCADO CORRECTO (punto ciego del modelo) — PASAR`**

| Métrica | Modelo | Mercado (Polymarket) | Opta |
|---|---|---|---|
| 1X2 (90 min) | CAN 32% / Emp 30% / MAR 37% | 17% / 28% / 54% | **MAR 51.8% / Emp 26.5% / CAN 21.7%** |
| Avanzar | CAN 47% / MAR 53% | — | **MAR 67% / CAN 33%** |
| O2.5 / BTTS | 33% / 40% | — | — |

**Clasificación:** la divergencia de +15pp a favor de Canadá se explica por **dos puntos ciegos nombrados**: (1) **localía fantasma** — el partido es en Houston (NRG, techo cerrado + A/C, sin calor) con hinchada **inclinada a Marruecos** (gran diáspora); el modelo aplica ventaja de anfitrión a Canadá que en la cancha no existe. (2) **brecha de calidad** — Marruecos (semifinalista '22, invicto en 4, 0.8 xGA/partido) es objetivamente mejor. **Opta (51.8%) y Polymarket ($6.3M, 54%) coinciden entre sí y contra nuestro modelo** → patrón dos-modelos-vs-uno = nuestro modelo es el equivocado. **Penales:** Bono, el mejor GK de shootout del mundo (Marruecos 2/2 recientes); Canadá sin historial. **PASAR** (lean Marruecos si se obliga). Sin bet de totales: el techo con A/C invalida el under por calor.

---

## 🔵 2. Paraguay vs Francia — 4 de Julio, 5:00 PM ET · Lincoln Financial Field, Filadelfia
**`MERCADO CORRECTO (punto ciego) — PASAR`**

| Métrica | Modelo | Mercado (Polymarket) | Opta |
|---|---|---|---|
| 1X2 (90 min) | PAR 14% / Emp 25% / FRA 61% | 4.5% / 12.5% / 83% | **FRA ~80% / Emp ~13% / PAR ~7%** |
| Avanzar | PAR 24% / FRA 76% | ~15% / ~85% | **FRA 86.6% / PAR 13.4%** |
| O2.5 / BTTS | 38% / 37% | — | — |

**Clasificación:** sesgo clásico de subvaloración de favorito. Francia va **casi a máxima fuerza** — Mbappé titular; Thuram (pantorrilla) y Tchouaméni (muslo) fuera son LESIONES, no rotación → **no hay edge de "favorito descansando"**. Opta (86.6% avanzar) ≈ Polymarket (~85%); nuestro 76% es el outlier (patrón Egipto-Irán). El **empate** tampoco tiene valor: Opta también lo pone en ~13%, así que el mercado NO lo subvalora aquí. Calor extremo en Filadelfia (~38°C, estadio abierto, 5PM) → leve inclinación a Under, pero **no se apuestan unders con este modelo**. Penales: Paraguay 2/2 en Mundiales (venció a Alemania), pero para llegar debe aguantar 90'+ a Francia — improbable. **PASAR** en todos los mercados.

---

## 🔵 3. Brasil vs Noruega — 5 de Julio, 4:00 PM ET · MetLife Stadium, Nueva Jersey
**`MERCADO CORRECTO (punto ciego confirmado, divergencia inversa) — PASAR`**

| Métrica | Modelo | Mercado (Polymarket) | Opta |
|---|---|---|---|
| 1X2 (90 min) | BRA 62% / Emp 23% / NOR 15% | 53% / 26% / 20% | **BRA 53.6% / Emp 24% / NOR 22.4%** |
| Avanzar | BRA 76% / NOR 24% | ~64% / ~36% | **BRA 65.6% / NOR 34.5%** |
| O2.5 / BTTS | 46% / 43% | — | — |

**Clasificación:** aquí el modelo está POR ENCIMA del mercado (raro) — y es punto ciego. Brasil **sin Raphinha (fuera del torneo) ni Paquetá (~3 semanas, su enlace creativo)**, Casemiro en duda; Noruega **completa con Haaland (5 goles en 4) + Ødegaard**. El modelo goles-only no ve las lesiones ni la forma individual de Haaland. **Opta (53.6% / 65.6% avanzar) es casi idéntico al mercado**; nuestro 62%/76% es el outlier. **PASAR** en ambos lados. Penales: Brasil 8V-7L histórico; Noruega sin ningún shootout mundialista — ventaja modesta Brasil. Vigilar Casemiro en la alineación (si está fuera, leve lean a Noruega-avanzar/empate).

---

## 🔵 5. Portugal vs España — 6 de Julio, 3:00 PM ET · AT&T Stadium, Arlington
**`MERCADO CORRECTO (punto ciego) — PASAR`**

| Métrica | Modelo | Mercado (Polymarket, fino $0.3M) | Opta / Casas |
|---|---|---|---|
| 1X2 (90 min) | POR 30% / Emp 27% / ESP 44% | 22% / 26% / 51% | ESP ~50% (todos coinciden) |
| Avanzar | POR 42% / ESP 58% | — | ESP ~66% (casas -220) |
| O2.5 / BTTS | 45% / 49% | — | — |

**Clasificación:** subvaloración de favorito. España domina (defensa sólida, Rodri apto, Oyarzábal cogoleador, Yamal en su techo) — cosas que un modelo de goles no pesa. **Nico Williams (aductor) fuera**, pero España era favorita igual → ya está en precio. Polymarket ~51%, DraftKings ~48%, Opta convergen; nuestro modelo es el outlier. Techo cerrado con A/C → clima irrelevante. **Nota real de penales (no apostable):** Portugal tiene récord perfecto reciente y **venció a España 5-3 en la final de Nations League 2025**; España **1V-4L** en Mundiales (el peor). Pero la línea de "avanzar" ya lo descuenta y no hay vehículo limpio. **PASAR.**

---

## 🔵 7. Argentina vs Egipto — 7 de Julio, 12:00 PM ET · Mercedes-Benz Stadium, Atlanta
**`MERCADO CORRECTO — PASAR (tesis Salah falsificada)`**

| Métrica | Modelo | Mercado (Polymarket, fino/nuevo) | Casas |
|---|---|---|---|
| 1X2 (90 min) | ARG 65% / Emp 24% / EGY 11% | 71% / 20% / 9% | ARG ~72% / Emp ~21% / EGY ~17% |
| Avanzar | ARG 80% / EGY 20% | — | **ARG ~83-85%** |
| O2.5 / BTTS | 35% / 31% | — | — |

**Clasificación:** divergencia pequeña (subvaloración de favorito). **La tesis Salah está falsificada** — Salah fue titular, jugó 120 min vs Australia y **anotó de Panenka en la tanda**, así que Egipto NO está debilitado. Estadio techado (Atlanta) → sin factor calor. Consenso de casas (Polymarket es $0/fino aquí) tiene a Argentina ~83-85% para avanzar vs nuestro 80% — solo el sesgo habitual. Penales: **Argentina 6V-1L (el mejor de la historia), Dibu Martínez** — ya en precio. Under 2.5 tiene un ángulo narrativo (ambos jugaron 120 min hace 4 días) pero **no se apuestan unders con este modelo**. **PASAR.**

---

## 🔵 8. Suiza vs Colombia — 7 de Julio, 4:00 PM ET · BC Place, Vancouver
**`MERCADO CORRECTO (punto ciego) — PASAR`**

| Métrica | Modelo | Mercado (Polymarket, fino/nuevo) | 2º modelo |
|---|---|---|---|
| 1X2 (90 min) | SUI 26% / Emp 27% / COL 47% | 27% / 30% / 42% | Kalshi COL ~60% / SUI ~43% |
| Avanzar | SUI 39% / COL 61% | — | BetMGM COL ~55% |
| O2.5 / BTTS | 42% / 46% | — | — |

**Clasificación:** casi alineado; el mercado tiene a Colombia levemente por debajo del modelo porque ve lo que el modelo no: **Colombia jugó el 4 jul en Kansas City y debe volar a Vancouver — 2 días menos de descanso y el plantel más viajado del torneo**, mientras Suiza lleva 5 días en Vancouver sin moverse. Además **James Rodríguez** fue sustituido al descanso vs Ghana (táctico; 0 goles/asist. en el torneo) — su rol es incierto hasta la alineación. Techo cerrado → sin clima. Kalshi ≈ nuestro modelo; nada contradice la dirección. Penales: ambos 0-1 en Mundiales — simétrico, sin ventaja. **PASAR** (revisar en la alineación; mercado fino y blando).

---

## Resumen Ejecutivo de Apuestas

| Partido | Apuesta | Estado | Confianza | Clasificación |
|---|---|---|---|---|
| **MEX vs ENG** | 🔥 Inglaterra para Avanzar (Polymarket, 1u) | **APOSTAR** | ⭐⭐⭐ | EDGE triangulado (casas+Opta > Polymkt) |
| **USA vs BEL** | Bélgica para Avanzar (mínimo) | **VIGILAR** | ⭐⭐ | Edge degradado (modelo alto + Bélgica con suerte) |
| CAN vs MAR | — | PASAR | — | Localía fantasma + brecha de calidad (Opta coincide) |
| PAR vs FRA | — | PASAR | — | Francia a máxima fuerza (Opta 87%) |
| BRA vs NOR | — | PASAR | — | Lesiones BRA + forma Haaland (Opta = mercado) |
| POR vs ESP | — | PASAR | — | Clase de España (todos ~50%) |
| ARG vs EGY | — | PASAR | — | Salah apto; Argentina bien valuada |
| SUI vs COL | — | PASAR | — | Viaje/descanso COL + duda James |

> [!NOTE]
> **Regla rectora (skill `edge-finder`): divergencia ≠ valor.** En un mercado líquido de vig casi cero, la divergencia por defecto es un punto ciego del modelo, no una apuesta +EV. Las dos únicas jugadas son sesgos de mercado *estructurales* (Polymarket subvalora el "avanzar" del rival del anfitrión), confirmados por un segundo estimador independiente por encima de la línea blanda. Todo lo demás: PASAR es el output correcto — y las pasadas son alfa.
