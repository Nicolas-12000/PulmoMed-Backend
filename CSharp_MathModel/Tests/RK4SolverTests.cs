/*
 * RK4SolverTests.cs
 * Tests unitarios para RK4Solver
 * 
 * Valida: Precisión numérica, ecuaciones conocidas, estabilidad
 */

using NUnit.Framework;
using System;
using LungCancerVR.MathModel;

namespace LungCancerVR.Tests
{
    [TestFixture]
    public class RK4SolverTests
    {
        private RK4Solver solver;
        
        [SetUp]
        public void Setup()
        {
            solver = new RK4Solver();
        }
        
        // Ecuación simple: dy/dt = y, solución: y(t) = y0 * e^t
        private float[] ExponentialDerivative(float t, float[] y)
        {
            return new float[] { y[0] };
        }
        
        [Test]
        public void RK4Solver_ExponentialGrowth_Accurate()
        {
            float t0 = 0.0f;
            float[] y0 = { 1.0f };
            float t1 = 1.0f;
            
            float[] result = solver.Integrate(t0, y0, t1, ExponentialDerivative);
            
            // Solución exacta: e^1 ≈ 2.718
            float expected = (float)Math.Exp(1.0);
            Assert.AreEqual(expected, result[0], 0.01f); // 1% error
        }
        
        // Ecuación: dy/dt = -k*y (decaimiento exponencial)
        private float[] DecayDerivative(float t, float[] y)
        {
            float k = 0.5f;
            return new float[] { -k * y[0] };
        }
        
        [Test]
        public void RK4Solver_ExponentialDecay_Accurate()
        {
            float t0 = 0.0f;
            float[] y0 = { 100.0f };
            float t1 = 2.0f;
            
            float[] result = solver.Integrate(t0, y0, t1, DecayDerivative);
            
            // Solución: y(t) = 100 * e^(-0.5*2) = 100 * e^(-1) ≈ 36.79
            float expected = 100.0f * (float)Math.Exp(-1.0);
            Assert.AreEqual(expected, result[0], 1.0f);
        }
        
        // Oscilador armónico: d²x/dt² = -ω²x
        // Estado: [x, v], derivadas: [v, -ω²x]
        private float[] HarmonicOscillator(float t, float[] state)
        {
            float x = state[0];
            float v = state[1];
            float omega = 1.0f;
            
            return new float[] { v, -omega * omega * x };
        }
        
        [Test]
        public void RK4Solver_HarmonicOscillator_ConservesEnergy()
        {
            float t0 = 0.0f;
            float[] y0 = { 1.0f, 0.0f }; // x=1, v=0
            
            float initialEnergy = 0.5f * (y0[0] * y0[0] + y0[1] * y0[1]);
            
            // Simular período completo (2π)
            float t1 = (float)(2.0 * Math.PI);
            float[] result = solver.Integrate(t0, y0, t1, HarmonicOscillator, stepSize: 0.01f);
            
            float finalEnergy = 0.5f * (result[0] * result[0] + result[1] * result[1]);
            
            // Energía debe conservarse (error < 5%)
            Assert.AreEqual(initialEnergy, finalEnergy, initialEnergy * 0.05f);
        }
        
        [Test]
        public void RK4Solver_Step_SingleStep()
        {
            float[] y = { 1.0f };
            float t = 0.0f;
            float dt = 0.1f;
            
            float[] result = solver.Step(t, y, dt, ExponentialDerivative);
            
            Assert.IsNotNull(result);
            Assert.AreEqual(1, result.Length);
            Assert.Greater(result[0], y[0]); // Debe crecer
        }
        
        [Test]
        public void RK4Solver_MultipleSteps_ConsistentWithSingleStep()
        {
            float[] y0 = { 1.0f };
            float t0 = 0.0f;
            float dt = 0.1f;
            
            // Dos pasos de dt
            float[] y1 = solver.Step(t0, y0, dt, ExponentialDerivative);
            float[] y2 = solver.Step(t0 + dt, y1, dt, ExponentialDerivative);
            
            // Un paso de 2*dt
            float[] y_direct = solver.Step(t0, y0, 2 * dt, ExponentialDerivative);
            
            // Resultados similares (error por discretización)
            Assert.AreEqual(y2[0], y_direct[0], 0.01f);
        }
        
        [Test]
        public void RK4Solver_IntegrateWithHistory_ReturnsTrajectory()
        {
            float t0 = 0.0f;
            float[] y0 = { 1.0f };
            float t1 = 1.0f;
            float dt = 0.1f;
            
            float[][] history = solver.IntegrateWithHistory(
                t0, y0, t1, ExponentialDerivative, dt
            );
            
            Assert.IsNotNull(history);
            Assert.Greater(history.Length, 1);
            
            // Primer valor es condición inicial
            Assert.AreEqual(y0[0], history[0][0], 0.001f);
            
            // Valores crecientes
            for (int i = 1; i < history.Length; i++)
            {
                Assert.Greater(history[i][0], history[i - 1][0]);
            }
        }
        
        [Test]
        public void RK4Solver_SmallStepSize_MoreAccurate()
        {
            float t0 = 0.0f;
            float[] y0 = { 1.0f };
            float t1 = 1.0f;
            float exact = (float)Math.Exp(1.0);
            
            // Paso grande
            float[] result_large = solver.Integrate(
                t0, y0, t1, ExponentialDerivative, stepSize: 0.1f
            );
            float error_large = Math.Abs(result_large[0] - exact);
            
            // Paso pequeño
            float[] result_small = solver.Integrate(
                t0, y0, t1, ExponentialDerivative, stepSize: 0.01f
            );
            float error_small = Math.Abs(result_small[0] - exact);
            
            // Paso pequeño debe ser más preciso
            Assert.Less(error_small, error_large);
        }
        
        [Test]
        public void RK4Solver_NegativeTime_Backward()
        {
            float t0 = 1.0f;
            float[] y0 = { (float)Math.Exp(1.0) };
            float t1 = 0.0f; // Backward
            
            float[] result = solver.Integrate(t0, y0, t1, ExponentialDerivative);
            
            // Debe llegar cerca de 1.0
            Assert.AreEqual(1.0f, result[0], 0.1f);
        }
        
        [Test]
        public void RK4Solver_ZeroDerivative_NoChange()
        {
            float[] ZeroDerivative(float t, float[] y)
            {
                return new float[] { 0.0f };
            }
            
            float t0 = 0.0f;
            float[] y0 = { 5.0f };
            float t1 = 10.0f;
            
            float[] result = solver.Integrate(t0, y0, t1, ZeroDerivative);
            
            Assert.AreEqual(y0[0], result[0], 0.001f);
        }
        
        [Test]
        public void RK4Solver_MultiDimensional_TwoVariables()
        {
            float[] TwoDimDerivative(float t, float[] y)
            {
                return new float[] { y[1], -y[0] }; // Oscilador
            }
            
            float t0 = 0.0f;
            float[] y0 = { 1.0f, 0.0f };
            float t1 = 1.0f;
            
            float[] result = solver.Integrate(t0, y0, t1, TwoDimDerivative);
            
            Assert.AreEqual(2, result.Length);
        }
    }
}
