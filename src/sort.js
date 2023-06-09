const compoundIdSort = (compoundIdsArray) => {
  compoundIdsArray.sort((a, b) => {
    const matchA = a.match(/FT(\d+)/)
    const matchB = b.match(/FT(\d+)/)

    const numA = matchA ? Number(matchA[1]) : 0
    const numB = matchB ? Number(matchB[1]) : 0
    return numB - numA
  })
}

export { compoundIdSort }
