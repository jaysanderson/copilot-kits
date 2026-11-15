const nodeDraftProperties = {
  prefLabel: { type: 'string' as const, description: 'Preferred label for this taxonomy node' },
  altLabels: { type: 'array' as const, items: { type: 'string' as const }, description: 'Alternative labels or synonyms' },
  definition: { type: 'string' as const, description: 'Short definition of this category' },
  seedQueries: { type: 'array' as const, items: { type: 'string' as const }, description: 'Search queries to find documents in this category' },
};

const nodeDraftRequired = ['prefLabel', 'altLabels', 'definition', 'seedQueries'];

export const nodeDraftJsonSchema = {
  type: 'object' as const,
  required: nodeDraftRequired,
  properties: nodeDraftProperties,
  additionalProperties: false as const,
};

export const topLevelJsonSchema = {
  name: 'top_level_taxonomy',
  description: 'Top-level taxonomy categories derived from the document corpus',
  parameters: {
    type: 'object' as const,
    required: ['nodes'],
    properties: {
      nodes: {
        type: 'array' as const,
        items: nodeDraftJsonSchema,
        description: 'Array of top-level taxonomy nodes',
      },
    },
    additionalProperties: false as const,
  },
};

export const childrenJsonSchema = {
  name: 'children_taxonomy',
  description: 'Child taxonomy nodes that subdivide a parent category',
  parameters: {
    type: 'object' as const,
    required: ['children'],
    properties: {
      children: {
        type: 'array' as const,
        items: nodeDraftJsonSchema,
        description: 'Child taxonomy nodes',
      },
    },
    additionalProperties: false as const,
  },
};
