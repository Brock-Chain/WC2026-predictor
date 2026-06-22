# Feedback UI/UX para Reporte HTML (wc2026_predictions.html)

## Mejoras de Comprensión de Datos
1. **Tooltips Dinámicos e Instantáneos en el Heatmap:** Reemplazar el atributo nativo `title` por un tooltip flotante personalizado con JS/CSS para mostrar inmediatamente la probabilidad de cada marcador al pasar el cursor (ej. "Marcador: 2 - 1 | Probabilidad: 9.8%").
2. **Explicación Visual del Modelo (Fuerzas Latentes):** Mostrar la Fuerza de Ataque vs Fuerza de Defensa aprendida por el modelo para cada equipo, ayudando a explicar por qué se proyecta cierta cantidad de goles.
3. **Resolver la Paradoja 1-1 vs Favorito 1X2:** Agregar un indicador (ej. icono ⓘ) cuando el marcador más probable es un empate pero la probabilidad acumulada favorece a un equipo. Explicar brevemente que la suma de todos los escenarios de victoria supera a los escenarios de empate.
4. **Simulador Interactivo de Resultados ("What If?"):** Permitir a los usuarios hacer clic en marcadores hipotéticos para ver cómo se actualizarían las probabilidades de avanzar de la fase de grupos en tiempo real.
5. **Indicador de "Value" (Apuestas):** Si se integra con cuotas reales de mercado, resaltar dónde el porcentaje del modelo es mayor que la probabilidad implícita de la casa de apuestas (High Value Pick).
6. **Mayor Diagnóstico y Explicación de Goles:** Ampliar la sección de goles. En lugar de solo mostrar "Over 2.5", agregar un desglose mayor y explicar visualmente o mediante texto corto el diagnóstico del modelo (es decir, justificar por qué se espera que sea un partido abierto de muchos goles o muy cerrado).

## Mejoras de Navegación y Usabilidad
7. **Buscador de Equipos:** Añadir un input de búsqueda en la barra superior que filtre instantáneamente las tarjetas de los partidos y grupos para encontrar a cualquier selección fácilmente entre los 48 equipos.
8. **Visualización de Horarios en EST:** Incluir explícitamente los horarios de los partidos (actualmente solo se muestra la fecha) y mostrarlos estandarizados en la zona horaria **EST** (Eastern Standard Time).
9. **Accesibilidad (a11y) de la Escala de Colores:** Asegurar que la rampa de colores del heatmap y la barra 1X2 tengan contraste suficiente y sean interpretables para usuarios con daltonismo, sumando texturas sutiles si es necesario.
