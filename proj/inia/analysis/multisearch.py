from inia.models import IniaGene, SpeciesType, Dataset, Homologene

def multisearch_results(gene_symbols, species=None, inia_genes_only=False):
    '''
    :param gene_symbols: list of gene symbols, string. Speices = Species.SpeciesType
    :param inia_genes_only: when set to true, jsut returns the queryset instead of grouping.
    :return: Relevant genes across all datasets that match.  Grouped by homologene id as hg_idnum, also searches homologenes
    given a species.  If no species specified then homologenes can be whatever, free willie it.
    '''

    gene_symbols = set(gene_symbols)
    result_table = []
    all_genes = IniaGene.objects.none()
    not_found = []

    # generates a row for the result table for each search gene
    # TODO: Use Q filter instead of looping like this to reduce number of queries per input.
    # TODO: maybe serialize the actual results instead of re-running them woul dbe more effective?
    for symbol in gene_symbols:
        row = {}
        # Specify species here is important.
        hgenes = Homologene.objects.filter(gene_symbol__iexact=symbol, species=species).prefetch_related('iniagene_set')
        inia_hgene_set = IniaGene.objects.none()
        for hgene in hgenes:
            inia_hgene_set = inia_hgene_set.union(hgene.iniagene_set.all())

        qset = IniaGene.objects.filter(gene_symbol__iexact=symbol,
                                       dataset__species=species).prefetch_related('homologenes', 'dataset').order_by('dataset__name',
                                                                                                                     'homologenes__gene_symbol')
        qset = (qset.union(inia_hgene_set)).distinct()


        if qset:
            gene = qset[0]
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
            all_genes = all_genes.union(qset)
        if not qset:
            not_found.append(symbol)
    result_table = sorted(result_table, key=lambda k: k['num_datasets'], reverse=True)
    if inia_genes_only:
        return all_genes.distinct()
    return result_table, not_found
