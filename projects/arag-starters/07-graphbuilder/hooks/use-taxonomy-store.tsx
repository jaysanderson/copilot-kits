'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { TaxonomyModel, TaxonomyNode, TaxonomySettings, TaxonomyScheme, TaxonomyMetrics } from '@/lib/types';

/**
 * Single-project local persistence, shared across every tab of the app via
 * React Context. This is a one-person internal tool with no multi-user or
 * auth requirement, so the project lives in the browser's own localStorage
 * rather than a hosted database - one fewer moving part, one fewer secret.
 *
 * All five tab panels (Connect/Settings/Generate/Review/Export) render at
 * once inside the Tabs component, so they must share ONE instance of this
 * state, not five independent copies each reading localStorage once on
 * mount - otherwise a write made from the Generate tab is invisible to the
 * already-mounted Review/Export tabs until a full page reload.
 *
 * Every mutation also reads its "current" value from a ref, not from a
 * closure-captured state variable: a caller that awaits real async work
 * (a generation run) between two store calls - update status to
 * "generating", run generation, save nodes, update status to "complete" -
 * would otherwise have each call's `{...model, ...}` spread stale-overwrite
 * the previous call's write, because React state updates are not visible
 * inside an already-created callback closure. The ref is updated
 * synchronously on every commit, so sequential calls always compose
 * correctly regardless of render timing.
 */
const STORAGE_KEY = 'arag-taxonomy-builder:project';

interface StoredProject {
  id: string;
  status: string;
  model: TaxonomyModel;
}

function loadStored(): StoredProject | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as StoredProject;
  } catch {
    return null;
  }
}

function saveStored(project: StoredProject | null) {
  if (typeof window === 'undefined') return;
  try {
    if (project) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(project));
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // Storage can be unavailable (private browsing, quota) - the in-memory
    // state still works for the current session, it just won't persist.
  }
}

function newId(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `project-${Date.now()}`;
}

interface TaxonomyStoreValue {
  projectId: string | null;
  model: TaxonomyModel | null;
  status: string;
  loading: boolean;
  createProject: (scheme: TaxonomyScheme, settings: TaxonomySettings) => Promise<string>;
  updateProject: (updates: {
    status?: string;
    settings?: TaxonomySettings;
    metrics?: TaxonomyMetrics;
    title?: string;
    language?: string;
    baseUri?: string;
  }) => Promise<void>;
  saveNodes: (nodes: TaxonomyNode[]) => Promise<void>;
  updateNode: (nodeId: string, updates: Partial<TaxonomyNode>) => Promise<void>;
  deleteNode: (nodeId: string) => Promise<void>;
  loadFromJson: (imported: TaxonomyModel) => Promise<void>;
  resetProject: () => void;
  reload: () => void;
}

const TaxonomyStoreContext = createContext<TaxonomyStoreValue | null>(null);

export function TaxonomyStoreProvider({ children }: { children: React.ReactNode }) {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [model, setModel] = useState<TaxonomyModel | null>(null);
  const [status, setStatus] = useState<string>('draft');
  const [loading, setLoading] = useState(true);

  // Mirrors state synchronously so sequential mutations in the same async
  // caller always read the latest value - see the module comment above.
  const projectIdRef = useRef<string | null>(null);
  const modelRef = useRef<TaxonomyModel | null>(null);
  const statusRef = useRef<string>('draft');

  const commit = useCallback((id: string | null, nextStatus: string, nextModel: TaxonomyModel | null) => {
    projectIdRef.current = id;
    statusRef.current = nextStatus;
    modelRef.current = nextModel;
    setProjectId(id);
    setStatus(nextStatus);
    setModel(nextModel);
    saveStored(id && nextModel ? { id, status: nextStatus, model: nextModel } : null);
  }, []);

  const reload = useCallback(() => {
    setLoading(true);
    const stored = loadStored();
    if (stored) {
      commit(stored.id, stored.status, stored.model);
    }
    setLoading(false);
  }, [commit]);

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const createProject = useCallback(async (scheme: TaxonomyScheme, settings: TaxonomySettings) => {
    const id = newId();
    const createdAt = new Date().toISOString();
    const newModel: TaxonomyModel = {
      scheme: { ...scheme, id, createdAt },
      nodes: [],
      settings,
      metrics: { generationSeconds: 0 },
    };
    commit(id, 'draft', newModel);
    return id;
  }, [commit]);

  const updateProject = useCallback(async (updates: {
    status?: string;
    settings?: TaxonomySettings;
    metrics?: TaxonomyMetrics;
    title?: string;
    language?: string;
    baseUri?: string;
  }) => {
    const currentId = projectIdRef.current;
    const current = modelRef.current;
    if (!currentId || !current) return;

    const updated: TaxonomyModel = { ...current };
    if (updates.settings) updated.settings = updates.settings;
    if (updates.metrics) updated.metrics = updates.metrics;
    if (updates.title) updated.scheme = { ...updated.scheme, title: updates.title };
    if (updates.language) updated.scheme = { ...updated.scheme, language: updates.language };
    if (updates.baseUri) updated.scheme = { ...updated.scheme, baseUri: updates.baseUri };

    commit(currentId, updates.status ?? statusRef.current, updated);
  }, [commit]);

  const saveNodes = useCallback(async (nodes: TaxonomyNode[]) => {
    const currentId = projectIdRef.current;
    const current = modelRef.current;
    if (!currentId || !current) return;
    commit(currentId, statusRef.current, { ...current, nodes });
  }, [commit]);

  const updateNode = useCallback(async (nodeId: string, updates: Partial<TaxonomyNode>) => {
    const currentId = projectIdRef.current;
    const current = modelRef.current;
    if (!currentId || !current) return;
    const updatedNodes = current.nodes.map(n => (n.id === nodeId ? { ...n, ...updates } : n));
    commit(currentId, statusRef.current, { ...current, nodes: updatedNodes });
  }, [commit]);

  const deleteNode = useCallback(async (nodeId: string) => {
    const currentId = projectIdRef.current;
    const current = modelRef.current;
    if (!currentId || !current) return;

    const idsToDelete = new Set<string>();
    const collectDescendants = (id: string) => {
      idsToDelete.add(id);
      current.nodes.filter(n => n.parentId === id).forEach(n => collectDescendants(n.id));
    };
    collectDescendants(nodeId);

    const updatedNodes = current.nodes.filter(n => !idsToDelete.has(n.id));
    commit(currentId, statusRef.current, { ...current, nodes: updatedNodes });
  }, [commit]);

  const loadFromJson = useCallback(async (imported: TaxonomyModel) => {
    const id = newId();
    commit(id, 'complete', { ...imported, scheme: { ...imported.scheme, id } });
  }, [commit]);

  const resetProject = useCallback(() => {
    commit(null, 'draft', null);
  }, [commit]);

  const value = useMemo<TaxonomyStoreValue>(() => ({
    projectId,
    model,
    status,
    loading,
    createProject,
    updateProject,
    saveNodes,
    updateNode,
    deleteNode,
    loadFromJson,
    resetProject,
    reload,
  }), [projectId, model, status, loading, createProject, updateProject, saveNodes, updateNode, deleteNode, loadFromJson, resetProject, reload]);

  return (
    <TaxonomyStoreContext.Provider value={value}>
      {children}
    </TaxonomyStoreContext.Provider>
  );
}

export function useTaxonomyStore(): TaxonomyStoreValue {
  const ctx = useContext(TaxonomyStoreContext);
  if (!ctx) {
    throw new Error('useTaxonomyStore must be used within a TaxonomyStoreProvider');
  }
  return ctx;
}
