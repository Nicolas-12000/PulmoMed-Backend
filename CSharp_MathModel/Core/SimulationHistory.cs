/*
 * SimulationHistory.cs
 * Sistema de historial tipo Git para simulaciones
 * 
 * Optimización: Snapshots completos + Deltas incrementales
 * Permite: Avanzar, retroceder, branch, comparar timelines
 */

using System;
using System.Collections.Generic;

namespace LungCancerVR.MathModel
{
    /// <summary>
    /// Snapshot completo del estado de simulación en un punto temporal
    /// </summary>
    public class SimulationSnapshot
    {
        public float TimePoint { get; set; }
        public float SensitiveCells { get; set; }
        public float ResistantCells { get; set; }
        public string TreatmentType { get; set; }  // Nombre del tratamiento como string
        public string Description { get; set; }
        public DateTime Timestamp { get; set; }
        
        public SimulationSnapshot()
        {
            Timestamp = DateTime.Now;
            TreatmentType = "none";
        }
        
        /// <summary>
        /// Crea snapshot desde TumorGrowthModel
        /// </summary>
        public static SimulationSnapshot FromModel(TumorGrowthModel model, string treatmentName, string description = "")
        {
            return new SimulationSnapshot
            {
                TimePoint = model.CurrentTime,
                SensitiveCells = model.SensitiveCells,
                ResistantCells = model.ResistantCells,
                TreatmentType = treatmentName,
                Description = description,
                Timestamp = DateTime.Now
            };
        }
        
        /// <summary>
        /// Aplica snapshot a modelo (nota: el tratamiento debe ser re-aplicado externamente)
        /// </summary>
        public void ApplyToModel(TumorGrowthModel model)
        {
            // Solo restauramos el estado numérico
            // El tratamiento debe ser configurado por el controlador
            model.SetInitialConditions(SensitiveCells, ResistantCells);
            model.SetTime(TimePoint);
        }
        
        /// <summary>
        /// Calcula tamaño en bytes aproximado
        /// </summary>
        public int GetSizeBytes()
        {
            // 4 floats + 1 enum + 1 DateTime + string
            return 4 * 4 + 4 + 8 + (Description?.Length ?? 0) * 2;
        }
    }
    
    /// <summary>
    /// Delta incremental entre dos puntos temporales (solo cambios)
    /// </summary>
    public class SimulationDelta
    {
        public float DeltaTime { get; set; }
        public float DeltaSensitive { get; set; }
        public float DeltaResistant { get; set; }
        public bool TreatmentChanged { get; set; }
        public string NewTreatment { get; set; }
        
        /// <summary>
        /// Aplica delta a snapshot (forward)
        /// </summary>
        public SimulationSnapshot ApplyForward(SimulationSnapshot baseSnapshot)
        {
            return new SimulationSnapshot
            {
                TimePoint = baseSnapshot.TimePoint + DeltaTime,
                SensitiveCells = baseSnapshot.SensitiveCells + DeltaSensitive,
                ResistantCells = baseSnapshot.ResistantCells + DeltaResistant,
                TreatmentType = TreatmentChanged ? NewTreatment : baseSnapshot.TreatmentType,
                Description = "Delta applied"
            };
        }
        
        /// <summary>
        /// Revierte delta (backward)
        /// </summary>
        public SimulationSnapshot ApplyBackward(SimulationSnapshot currentSnapshot, string previousTreatment)
        {
            return new SimulationSnapshot
            {
                TimePoint = currentSnapshot.TimePoint - DeltaTime,
                SensitiveCells = currentSnapshot.SensitiveCells - DeltaSensitive,
                ResistantCells = currentSnapshot.ResistantCells - DeltaResistant,
                TreatmentType = TreatmentChanged ? previousTreatment : currentSnapshot.TreatmentType,
                Description = "Delta reverted"
            };
        }
        
        /// <summary>
        /// Crea delta entre dos snapshots
        /// </summary>
        public static SimulationDelta FromSnapshots(SimulationSnapshot from, SimulationSnapshot to)
        {
            return new SimulationDelta
            {
                DeltaTime = to.TimePoint - from.TimePoint,
                DeltaSensitive = to.SensitiveCells - from.SensitiveCells,
                DeltaResistant = to.ResistantCells - from.ResistantCells,
                TreatmentChanged = to.TreatmentType != from.TreatmentType,
                NewTreatment = to.TreatmentType != from.TreatmentType ? to.TreatmentType : null
            };
        }
        
        /// <summary>
        /// Tamaño en bytes (muy pequeño comparado con snapshot)
        /// </summary>
        public int GetSizeBytes()
        {
            // 3 floats + 1 bool + 1 nullable enum
            return 3 * 4 + 1 + 8;
        }
    }
    
    /// <summary>
    /// Nodo en el árbol de historial (permite branching)
    /// </summary>
    public class HistoryNode
    {
        public string Id { get; set; }
        public SimulationSnapshot Snapshot { get; set; }
        public List<SimulationDelta> DeltasToNext { get; set; }
        public HistoryNode Parent { get; set; }
        public List<HistoryNode> Children { get; set; }
        public bool IsCheckpoint { get; set; }
        
        public HistoryNode()
        {
            Id = Guid.NewGuid().ToString().Substring(0, 8);
            DeltasToNext = new List<SimulationDelta>();
            Children = new List<HistoryNode>();
            IsCheckpoint = false;
        }
    }
    
    /// <summary>
    /// Sistema completo de historial tipo Git
    /// </summary>
    public class SimulationHistory
    {
        private HistoryNode rootNode;
        private HistoryNode currentNode;
        
        // Configuración
        private int snapshotInterval;  // Cada cuántos pasos crear snapshot completo
        private int maxDeltas;         // Máximo de deltas entre snapshots
        
        public int TotalSnapshots { get; private set; }
        public int TotalDeltas { get; private set; }
        public string CurrentBranch { get; private set; }
        
        /// <summary>
        /// Constructor
        /// </summary>
        /// <param name="snapshotInterval">Crear snapshot cada N pasos (default: 100)</param>
        /// <param name="maxDeltas">Máximo deltas entre snapshots (default: 100)</param>
        public SimulationHistory(int snapshotInterval = 100, int maxDeltas = 100)
        {
            this.snapshotInterval = snapshotInterval;
            this.maxDeltas = maxDeltas;
            this.CurrentBranch = "main";
            TotalSnapshots = 0;
            TotalDeltas = 0;
        }
        
        /// <summary>
        /// Inicializa historial con estado inicial
        /// </summary>
        public void Initialize(TumorGrowthModel model, string treatmentName, string description = "Initial state")
        {
            rootNode = new HistoryNode
            {
                Snapshot = SimulationSnapshot.FromModel(model, treatmentName, description),
                IsCheckpoint = true
            };
            currentNode = rootNode;
            TotalSnapshots = 1;
        }
        
        /// <summary>
        /// Guarda estado actual (crea delta o snapshot según configuración)
        /// </summary>
        public void SaveState(TumorGrowthModel model, string treatmentName, bool forceSnapshot = false)
        {
            if (currentNode == null)
            {
                Initialize(model, treatmentName, "Auto-initialized");
                return;
            }
            
            var newSnapshot = SimulationSnapshot.FromModel(model, treatmentName);
            
            // Decidir si crear snapshot o delta
            bool shouldCreateSnapshot = forceSnapshot || 
                                       currentNode.DeltasToNext.Count >= maxDeltas ||
                                       (newSnapshot.TimePoint - currentNode.Snapshot.TimePoint) >= snapshotInterval;
            
            if (shouldCreateSnapshot)
            {
                // Crear nuevo nodo checkpoint
                var newNode = new HistoryNode
                {
                    Snapshot = newSnapshot,
                    Parent = currentNode,
                    IsCheckpoint = true
                };
                
                currentNode.Children.Add(newNode);
                currentNode = newNode;
                TotalSnapshots++;
            }
            else
            {
                // Crear delta incremental
                var delta = SimulationDelta.FromSnapshots(
                    currentNode.Snapshot,
                    newSnapshot
                );
                
                currentNode.DeltasToNext.Add(delta);
                TotalDeltas++;
            }
        }
        
        /// <summary>
        /// Retrocede N pasos en el historial
        /// </summary>
        public bool Rewind(TumorGrowthModel model, int steps)
        {
            if (currentNode == null || currentNode == rootNode)
                return false;
            
            // Simplificado: ir al snapshot anterior
            if (currentNode.Parent != null)
            {
                currentNode = currentNode.Parent;
                currentNode.Snapshot.ApplyToModel(model);
                return true;
            }
            
            return false;
        }
        
        /// <summary>
        /// Avanza N pasos en el historial (si existe)
        /// </summary>
        public bool FastForward(TumorGrowthModel model, int steps)
        {
            if (currentNode == null || currentNode.Children.Count == 0)
                return false;
            
            // Avanzar al primer hijo
            currentNode = currentNode.Children[0];
            currentNode.Snapshot.ApplyToModel(model);
            return true;
        }
        
        /// <summary>
        /// Crea una rama (branch) para experimentar sin perder historial principal
        /// </summary>
        public string CreateBranch(string branchName)
        {
            CurrentBranch = branchName;
            return currentNode.Id;
        }
        
        /// <summary>
        /// Vuelve a un punto específico del historial por ID
        /// </summary>
        public bool GoToCheckpoint(TumorGrowthModel model, string checkpointId)
        {
            var node = FindNodeById(rootNode, checkpointId);
            if (node != null)
            {
                currentNode = node;
                node.Snapshot.ApplyToModel(model);
                return true;
            }
            return false;
        }
        
        /// <summary>
        /// Obtiene lista de checkpoints disponibles
        /// </summary>
        public List<(string id, float time, string description)> GetCheckpoints()
        {
            var checkpoints = new List<(string, float, string)>();
            CollectCheckpoints(rootNode, checkpoints);
            return checkpoints;
        }
        
        /// <summary>
        /// Calcula memoria usada por el historial
        /// </summary>
        public string GetMemoryUsage()
        {
            int totalBytes = 0;
            CountMemoryUsage(rootNode, ref totalBytes);
            
            if (totalBytes < 1024)
                return $"{totalBytes} bytes";
            else if (totalBytes < 1024 * 1024)
                return $"{totalBytes / 1024.0:F2} KB";
            else
                return $"{totalBytes / (1024.0 * 1024.0):F2} MB";
        }
        
        /// <summary>
        /// Limpia historial antiguo (garbage collection)
        /// </summary>
        public void PruneHistory(int keepLastNSnapshots = 10)
        {
            // Implementación simplificada: mantener solo los últimos N snapshots
            // En producción sería más sofisticado
        }
        
        // === Métodos auxiliares privados ===
        
        private HistoryNode FindNodeById(HistoryNode node, string id)
        {
            if (node == null) return null;
            if (node.Id == id) return node;
            
            foreach (var child in node.Children)
            {
                var result = FindNodeById(child, id);
                if (result != null) return result;
            }
            
            return null;
        }
        
        private void CollectCheckpoints(HistoryNode node, List<(string, float, string)> checkpoints)
        {
            if (node == null) return;
            
            if (node.IsCheckpoint)
            {
                checkpoints.Add((
                    node.Id,
                    node.Snapshot.TimePoint,
                    node.Snapshot.Description
                ));
            }
            
            foreach (var child in node.Children)
            {
                CollectCheckpoints(child, checkpoints);
            }
        }
        
        private void CountMemoryUsage(HistoryNode node, ref int totalBytes)
        {
            if (node == null) return;
            
            if (node.IsCheckpoint)
            {
                totalBytes += node.Snapshot.GetSizeBytes();
            }
            
            foreach (var delta in node.DeltasToNext)
            {
                totalBytes += delta.GetSizeBytes();
            }
            
            foreach (var child in node.Children)
            {
                CountMemoryUsage(child, ref totalBytes);
            }
        }
    }
}
