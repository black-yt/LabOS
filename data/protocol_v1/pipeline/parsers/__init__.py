from . import star, bioprot, nprot, jove, curprot, mimb, f1000

REGISTRY = {
    "star": star.parse,
    "bioprot": bioprot.parse,
    "nprot": nprot.parse,
    "curprot": curprot.parse,
    "mimb":    mimb.parse,
    "nmeth":   nprot.parse,
    "jove":    jove.parse,
    "f1000":   f1000.parse,
}
