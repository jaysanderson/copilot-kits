import type { TaxonomyModel, TaxonomyNode } from './types';

function escapeTurtle(str: string): string {
  return str
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r')
    .replace(/\t/g, '\\t');
}

function uri(value: string): string {
  return `<${value}>`;
}

export function exportSkosXlTurtle(model: TaxonomyModel): string {
  const { scheme, nodes } = model;
  const lang = scheme.language || 'en';
  const base = scheme.baseUri.endsWith('/') ? scheme.baseUri : `${scheme.baseUri}/`;
  const schemeUri = `${base}scheme/${scheme.id}`;

  const lines: string[] = [];

  lines.push('@prefix skos: <http://www.w3.org/2004/02/skos/core#> .');
  lines.push('@prefix skosxl: <http://www.w3.org/2008/05/skos-xl#> .');
  lines.push('@prefix dct: <http://purl.org/dc/terms/> .');
  lines.push('@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .');
  lines.push('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .');
  lines.push('@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .');
  lines.push('');

  const topNodes = nodes.filter(n => n.parentId === null);

  lines.push(`${uri(schemeUri)} a skos:ConceptScheme ;`);
  lines.push(`    dct:title "${escapeTurtle(scheme.title)}"@${lang} ;`);
  if (topNodes.length > 0) {
    const topRefs = topNodes.map(n => uri(`${base}concept/${n.id}`));
    lines.push(`    skos:hasTopConcept ${topRefs.join(' ,\n        ')} .`);
  } else {
    lines[lines.length - 1] = lines[lines.length - 1].replace(' ;', ' .');
  }
  lines.push('');

  for (const node of nodes) {
    const conceptUri = `${base}concept/${node.id}`;
    const prefLabelUri = `${base}label/${node.id}/pref`;

    lines.push(`${uri(conceptUri)} a skos:Concept ;`);
    lines.push(`    skos:inScheme ${uri(schemeUri)} ;`);

    if (node.parentId) {
      lines.push(`    skos:broader ${uri(`${base}concept/${node.parentId}`)} ;`);
    }

    lines.push(`    skosxl:prefLabel ${uri(prefLabelUri)} ;`);

    if (node.altLabels.length > 0) {
      const altRefs = node.altLabels.map((_, i) => uri(`${base}label/${node.id}/alt/${i}`));
      lines.push(`    skosxl:altLabel ${altRefs.join(' ,\n        ')} ;`);
    }

    if (node.definition) {
      lines.push(`    skos:definition "${escapeTurtle(node.definition)}"@${lang} ;`);
    }

    const lastLine = lines[lines.length - 1];
    lines[lines.length - 1] = lastLine.replace(/ ;$/, ' .');
    lines.push('');

    lines.push(`${uri(prefLabelUri)} a skosxl:Label ;`);
    lines.push(`    skosxl:literalForm "${escapeTurtle(node.prefLabel)}"@${lang} .`);
    lines.push('');

    node.altLabels.forEach((alt, i) => {
      const altUri = `${base}label/${node.id}/alt/${i}`;
      lines.push(`${uri(altUri)} a skosxl:Label ;`);
      lines.push(`    skosxl:literalForm "${escapeTurtle(alt)}"@${lang} .`);
      lines.push('');
    });
  }

  return lines.join('\n');
}
