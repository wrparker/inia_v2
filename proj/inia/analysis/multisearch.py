from inia.models import IniaGene, SpeciesType, Dataset

def multisearch_reults(gene_symbols, species=None):
    '''
    :param gene_symbols: list of gene symbols, string. Speices = Species.SpeciesType
    :return: Relevant genes across all datasets that match.  Grouped by homologene id as hg_idnum, also searches homologenes
    given a species.  If no species specified then homologenes can be whatever, free willie it.
    '''

    gene_symbols = set(gene_symbols)
    result_table = []

    # generates a row for the result table for each search gene
    for symbol in gene_symbols:
        row = {}
        qset = IniaGene.objects.filter(gene_symbol__iexact=symbol,
                                       dataset__species=species).prefetch_related('homologenes', 'dataset').order_by('dataset__name',
                                                                                                                     'homologenes__gene_symbol')
        if qset:
            gene = qset.first()
            datasets = [gene.dataset for gene in qset]
            if not gene.get_homologene_id():
                if gene.ncbi_uid:
                    row['ncbi_uid_query'] = '{}[GENE_UNIQUE_ID]'.format(gene.ncbi_uid)
                else:
                    row['ncbi_uid_query'] = gene.gene_symbol
                for i in SpeciesType.SPECIES_CHOICES:
                    if i[0] == species:
                        row[i[0]] = '{} *'.format(gene.gene_symbol)
                    else:
                        row[i[0]] = ''
            else:
                row[SpeciesType.HOMO_SAPIENS] = gene.list_human_orthologs()
                row[SpeciesType.MUS_MUSCULUS] = gene.list_mouse_orthologs()
                row[SpeciesType.RATTUS_NORVEGICUS] = gene.list_rat_orthologs()
                row['homologene_id'] = gene.get_homologene_id()
                datasets = Dataset.objects.filter(iniagene__homologenes__homologene_group_id=row['homologene_id']).order_by('name')

            row['datasets'] = set(datasets)
            count = 0
            for ds in row['datasets']:
                count += 1
            row['num_datasets'] = count
            result_table.append(row)
    result_table = sorted(result_table, key=lambda k: k['num_datasets'], reverse=True)
    return result_table
