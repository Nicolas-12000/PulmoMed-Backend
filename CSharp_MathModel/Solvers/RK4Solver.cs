/*
 * RK4Solver.cs
 * Integrador numérico Runge-Kutta de 4to orden para sistemas de ODEs
 * 
 * Usado para resolver las ecuaciones diferenciales de Gompertz:
 * dNs/dt = rs * Ns * ln(K/(Ns+Nr)) - β(t) * Ns
 * dNr/dt = rr * Nr * ln(K/(Ns+Nr))
 * 
 * RK4 es preciso, estable y eficiente para este tipo de sistemas
 */

using System;

namespace LungCancerVR.MathModel
{
    /// <summary>
    /// Delegado para funciones de derivada
    /// </summary>
    /// <param name="t">Tiempo actual</param>
    /// <param name="y">Vector de estado actual [Ns, Nr]</param>
    /// <returns>Derivadas [dNs/dt, dNr/dt]</returns>
    public delegate float[] DerivativeFunction(float t, float[] y);
    
    /// <summary>
    /// Solver Runge-Kutta de 4to orden
    /// Precisión O(h^4), robusto para sistemas stiff moderados
    /// </summary>
    public class RK4Solver
    {
        private DerivativeFunction derivativeFunc;
        private float stepSize;
        
        /// <summary>
        /// Constructor del solver
        /// </summary>
        /// <param name="derivativeFunc">Función que calcula derivadas</param>
        /// <param name="stepSize">Paso de integración (días). Default: 0.1</param>
        public RK4Solver(DerivativeFunction derivativeFunc, float stepSize = 0.1f)
        {
            this.derivativeFunc = derivativeFunc ?? throw new ArgumentNullException(nameof(derivativeFunc));
            
            if (stepSize <= 0 || stepSize > 1.0f)
                throw new ArgumentException("Step size debe estar en (0, 1.0] días");
            
            this.stepSize = stepSize;
        }
        
        /// <summary>
        /// Realiza un paso de integración RK4
        /// </summary>
        /// <param name="t">Tiempo actual</param>
        /// <param name="y">Estado actual [Ns, Nr]</param>
        /// <returns>Nuevo estado [Ns', Nr']</returns>
        public float[] Step(float t, float[] y)
        {
            if (y == null || y.Length != 2)
                throw new ArgumentException("Estado debe ser array de 2 elementos [Ns, Nr]");
            
            float h = stepSize;
            
            // Cálculo de pendientes RK4
            float[] k1 = derivativeFunc(t, y);
            
            float[] y_k2 = new float[2];
            y_k2[0] = y[0] + 0.5f * h * k1[0];
            y_k2[1] = y[1] + 0.5f * h * k1[1];
            float[] k2 = derivativeFunc(t + 0.5f * h, y_k2);
            
            float[] y_k3 = new float[2];
            y_k3[0] = y[0] + 0.5f * h * k2[0];
            y_k3[1] = y[1] + 0.5f * h * k2[1];
            float[] k3 = derivativeFunc(t + 0.5f * h, y_k3);
            
            float[] y_k4 = new float[2];
            y_k4[0] = y[0] + h * k3[0];
            y_k4[1] = y[1] + h * k3[1];
            float[] k4 = derivativeFunc(t + h, y_k4);
            
            // Combinación ponderada (1/6, 1/3, 1/3, 1/6)
            float[] yNext = new float[2];
            yNext[0] = y[0] + (h / 6.0f) * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0]);
            yNext[1] = y[1] + (h / 6.0f) * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1]);
            
            // Protección contra valores negativos (no físicos)
            yNext[0] = Math.Max(0, yNext[0]);
            yNext[1] = Math.Max(0, yNext[1]);
            
            return yNext;
        }
        
        /// <summary>
        /// Integra el sistema desde t0 hasta tFinal
        /// </summary>
        /// <param name="t0">Tiempo inicial</param>
        /// <param name="y0">Estado inicial [Ns0, Nr0]</param>
        /// <param name="tFinal">Tiempo final</param>
        /// <returns>Estado final [Ns(tFinal), Nr(tFinal)]</returns>
        public float[] Integrate(float t0, float[] y0, float tFinal)
        {
            if (tFinal < t0)
                throw new ArgumentException("tFinal debe ser >= t0");
            
            float t = t0;
            float[] y = (float[])y0.Clone();
            
            int maxSteps = (int)Math.Ceiling((tFinal - t0) / stepSize);
            
            for (int step = 0; step < maxSteps; step++)
            {
                if (t >= tFinal)
                    break;
                
                // Ajustar último paso si es necesario
                float currentStepSize = stepSize;
                if (t + stepSize > tFinal)
                {
                    currentStepSize = tFinal - t;
                    // Crear solver temporal con step ajustado
                    var tempSolver = new RK4Solver(derivativeFunc, currentStepSize);
                    y = tempSolver.Step(t, y);
                    t = tFinal;
                    break;
                }
                
                y = Step(t, y);
                t += stepSize;
            }
            
            return y;
        }
        
        /// <summary>
        /// Integra el sistema retornando trayectoria completa
        /// </summary>
        /// <param name="t0">Tiempo inicial</param>
        /// <param name="y0">Estado inicial</param>
        /// <param name="tFinal">Tiempo final</param>
        /// <param name="numPoints">Número de puntos a retornar</param>
        /// <returns>Arrays de tiempos, Ns, Nr</returns>
        public (float[] times, float[] Ns, float[] Nr) IntegrateWithHistory(
            float t0, float[] y0, float tFinal, int numPoints = 100)
        {
            if (numPoints < 2)
                throw new ArgumentException("numPoints debe ser >= 2");
            
            float[] times = new float[numPoints];
            float[] NsHistory = new float[numPoints];
            float[] NrHistory = new float[numPoints];
            
            float dt = (tFinal - t0) / (numPoints - 1);
            
            times[0] = t0;
            NsHistory[0] = y0[0];
            NrHistory[0] = y0[1];
            
            float t = t0;
            float[] y = (float[])y0.Clone();
            
            for (int i = 1; i < numPoints; i++)
            {
                float targetTime = t0 + i * dt;
                y = Integrate(t, y, targetTime);
                t = targetTime;
                
                times[i] = t;
                NsHistory[i] = y[0];
                NrHistory[i] = y[1];
            }
            
            return (times, NsHistory, NrHistory);
        }
    }
}
