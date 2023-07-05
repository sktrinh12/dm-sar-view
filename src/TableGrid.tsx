import * as React from 'react'
import Paper from '@mui/material/Paper'
import Table from '@mui/material/Table'
import TableContainer from '@mui/material/TableContainer'
import { TableDataType } from './types'
import { styled } from '@mui/system'

const TableRow = styled('tr')({
  fontSize: '12px',
})

export default function TableGrid({ tableData }: { tableData: TableDataType }) {
  return Object.keys(tableData).map((cmpdId, index) => (
    <div
      key={`div-row-${cmpdId}-${index}`}
      style={{
        display: 'flex',
        flexWrap: 'nowrap',
        borderTop: '1px solid black',
        paddingTop: '2px',
        marginTop: '2px',
      }}
    >
      {Object.keys(tableData[cmpdId]).map((key) => {
        const tdata = tableData[cmpdId][key]
        return (
          <div
            key={`div-${cmpdId}-${key}-${index}`}
            style={{ flex: '0 0 auto', margin: '6px' }}
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
                              borderBottomWidth: '2px',
                              borderBottomStyle: 'solid',
                              padding: '8px',
                            }}
                          >
                            {columnKey
                              .replace(/_/g, ' ')
                              .toLowerCase()
                              .replace(/\b\w/g, (match) => match.toUpperCase())}
                          </th>
                        ))
                    ) : (
                      <th
                        style={{
                          borderBottomWidth: '2px',
                          borderBottomStyle: 'solid',
                          padding: '8px',
                          minWidth: '200px',
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
                          const truncatedValue =
                            typeof value === 'number' ? value.toFixed(2) : value
                          const displayValue =
                            value !== null && value !== undefined
                              ? truncatedValue
                              : '-'
                          if (columnKey === 'MOLFILE') {
                            const link = `https://dotmatics.kinnate.com/browser/query/browse.jsp?currentPrimary=${cmpdId}`
                            return (
                              <td
                                key={`${cmpdId}-${columnKey}`}
                                style={{
                                  borderBottomWidth: '1px',
                                  borderBottomStyle: 'solid',
                                  padding: '8px',
                                  margin: 0,
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
                                padding: '8px',
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
