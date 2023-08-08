import * as React from 'react'
import Paper from '@mui/material/Paper'
import Table from '@mui/material/Table'
import TableContainer from '@mui/material/TableContainer'
import { TableDataType } from './types'
import { styled } from '@mui/system'
import ReactLoading from 'react-loading'
import { colour } from './Colour'

const TableRow = styled('tr')({
  fontSize: '13.5px',
})

const minWidthByKeys = {
  row: '40px',
  biochemical_geomean: '600px',
  cellular_geomean: '580px',
  in_vivo_pk: '350px',
  compound_batch: '120px',
  metabolic_stability: '340px',
  pxr: '250px',
  permeability: '425px',
  protein_binding: '300px',
  solubility: '100px',
  stability: '340px',
  mol_structure: '150px',
}

export default function TableGrid({
  tableData,
  bioLoading,
}: {
  tableData: TableDataType
  bioLoading: boolean
}) {
  return Object.keys(tableData).map((cmpdId, index) => (
    <div
      key={`div-row-${cmpdId}-${index}`}
      style={{
        paddingTop: '2px',
        marginTop: '2px',
        display: 'flex',
      }}
    >
      {Object.keys(tableData[cmpdId]).map((key) => {
        const tdata = tableData[cmpdId][key]
        return (
          <div
            key={`div-${cmpdId}-${key}-${index}`}
            style={{
              flex: '0 0 auto',
              margin: '4px',
              minWidth: minWidthByKeys[key] || '112px',
            }}
          >
            <h3>
              {key
                .replace(/_/g, ' ')
                .toLowerCase()
                .replace(/\b\w/g, (match) => match.toUpperCase())}
            </h3>
            <TableContainer key={`${cmpdId}-${key}-${index}`} component={Paper}>
              <Table sx={{ borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    {tdata.length > 0 ? (
                      Object.keys(tdata[0])
                        .filter((columnKey) => columnKey !== 'DATE_HIGHLIGHT')
                        .map((columnKey) => (
                          <th
                            key={columnKey}
                            style={{
                              borderTopWidth: '0.5px',
                              borderTopStyle: 'solid',
                              textAlign: 'left',
                              padding: '4px',
                            }}
                          >
                            {columnKey !== 'row' &&
                            columnKey !== 'FT_NUM' &&
                            columnKey !== 'MOLFILE'
                              ? columnKey
                                  .replace(/_/g, ' ')
                                  .toLowerCase()
                                  .replace(/\b\w/g, (match) =>
                                    match.toUpperCase()
                                  )
                              : '\u00A0'}
                          </th>
                        ))
                    ) : key === 'biochemical_geomean' && bioLoading ? (
                      <td>
                        <div
                          style={{
                            margin: 'auto',
                            padding: '4px',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                          }}
                        >
                          <ReactLoading
                            type='spin'
                            color={colour}
                            height={32}
                            width={32}
                          />
                        </div>
                      </td>
                    ) : (
                      <th
                        style={{
                          borderBottomWidth: '1px',
                          borderBottomStyle: 'solid',
                          padding: '4px',
                          minWidth: minWidthByKeys[key] || '200px',
                          opacity: 0.25,
                        }}
                      >
                        No data available
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {tdata.map((item, rowIndex: number) => (
                    <TableRow
                      key={rowIndex}
                      style={{
                        boxShadow:
                          item.DATE_HIGHLIGHT === 1
                            ? '0 0 8px rgba(0, 0, 255, 0.5)'
                            : 'none',

                        backgroundColor:
                          item.DATE_HIGHLIGHT === 1
                            ? 'rgba(0, 0, 255, 0.2)'
                            : 'transparent',
                      }}
                    >
                      {Object.keys(item)
                        .filter((columnKey) => columnKey !== 'DATE_HIGHLIGHT')
                        .map((columnKey) => {
                          const value = item[columnKey]
                          let displayValue: string
                          if (columnKey === 'Row') {
                            displayValue = Number.isInteger(value)
                              ? value.toString()
                              : '-'
                          } else {
                            let truncatedValue: string

                            if (typeof value === 'number') {
                              truncatedValue =
                                value % 1 === 0
                                  ? value.toString()
                                  : value.toFixed(2)
                            } else {
                              truncatedValue = value
                            }

                            displayValue =
                              value !== null && value !== undefined
                                ? truncatedValue
                                : '-'
                          }
                          if (columnKey === 'MOLFILE') {
                            const link = `https://dotmatics.kinnate.com/browser/query/browse.jsp?currentPrimary=${cmpdId}`
                            return (
                              <td
                                key={`${cmpdId}-${columnKey}`}
                                style={{
                                  borderBottomWidth: '1px',
                                  borderBottomStyle: 'solid',
                                  padding: '4px',
                                  margin: '2px',
                                }}
                              >
                                <a
                                  href={link}
                                  target='_blank'
                                  rel='noopener noreferrer'
                                >
                                  <div
                                    dangerouslySetInnerHTML={{
                                      __html: displayValue,
                                    }}
                                    style={{
                                      width: '100%',
                                      height: '100%',
                                    }}
                                  />
                                </a>
                              </td>
                            )
                          }

                          return (
                            <td
                              key={`${cmpdId}-${columnKey}`}
                              style={{
                                borderBottomWidth: '1px',
                                borderBottomStyle: 'solid',
                                padding: '3px',
                                margin: 0,
                              }}
                            >
                              {displayValue}
                            </td>
                          )
                        })}
                    </TableRow>
                  ))}
                </tbody>
              </Table>
            </TableContainer>
          </div>
        )
      })}
    </div>
  ))
}
