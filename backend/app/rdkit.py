from rdkit.Chem import MolFromMolBlock
from rdkit.Chem.Draw import rdMolDraw2D


def chem_draw(
    mol_str: str,
    size: int,
):
    try:
        svg = ""
        molecule = MolFromMolBlock(mol_str)
        if molecule:
            molecule = rdMolDraw2D.PrepareMolForDrawing(molecule)
            drawer = rdMolDraw2D.MolDraw2DSVG(size, size)
            drawer.drawOptions().addStereoAnnotation = True
            # drawer.drawOptions().addAtomIndices = True
            drawer.DrawMolecule(molecule)
            drawer.FinishDrawing()
            svg = drawer.GetDrawingText()
        return svg
    except Exception as ex:
        print(f"rdkit chem draw error: {ex}")
