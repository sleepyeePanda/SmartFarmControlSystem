# parameter placeholder
INSERT_SF_query = 'INSERT INTO data(ID, sfID, CO2, LUX, INTMP, INHUMID, DateTime) VALUES(?, ?, ?, ?, ?, ?, ?)'

INSERT_SENSOR_query = 'INSERT INTO data(ID, TMP, DO, PH, TDS, DateTime) VALUES(?, ?, ?, ?, ?, ?)'

INSERT_ELEC_query = 'INSERT INTO data(ID, ELEC, DateTime) VALUES(?,?,?)'

FETCH_SF_query = 'SELECT CO2, LUX, INTMP, INHUMID, DateTime\
                    FROM data\
                    WHERE sfID = ?\
                    AND CO2 IS NOT NULL\
                    AND LUX IS NOT NULL\
                    AND INTMP IS NOT NULL\
                    AND INHUMID IS NOT NULL\
                    AND DateTime IS NOT NULL\
                    ORDER BY DateTime DESC\
                    LIMIT 48'

FETCH_SF_query_ = 'SELECT avg(CO2), avg(LUX), avg(INTMP), avg(INHUMID), DateTime\
                    FROM data\
                    WHERE sfID = ?'

byWeek= " GROUP BY strftime('%Y-%m-%d %H',DateTime)\
        ORDER BY DateTime DESC\
        LIMIT 168"

byMonth = " GROUP BY strftime('%Y-%m-%d %H',DateTime)\
        HAVING strftime('%H',DateTime) = ? OR\
        strftime('%H',DateTime) = ? OR\
        strftime('%H',DateTime) = ? OR\
        strftime('%H',DateTime) = ?\
        ORDER BY DateTime DESC\
        LIMIT 168"

FETCH_ELEC_query = 'SELECT ELEC, DateTime\
                        FROM data\
                        WHERE ID = ?\
                        AND ELEC IS NOT NULL\
                        AND DateTime IS NOT NULL\
                        ORDER BY DateTime DESC\
                        LIMIT 48'

FETCH_ELEC_query_ = 'SELECT avg(ELEC), DateTime\
                        FROM data\
                        WHERE ID = ?'

FETCH_ELEC_query_byHour = "SELECT sum(ELEC)\
                                FROM data\
                                GROUP BY strftime('%Y-%m-%d %H',DateTime)\
                                ORDER BY DateTime DESC\
                                LIMIT 1"

FETCH_ELEC_query_byDay = "SELECT sum(ELEC)\
                                FROM data\
                                GROUP BY strftime('%Y-%m-%d',DateTime)\
                                ORDER BY DateTime DESC\
                                LIMIT 1"

FETCH_ELEC_query_byWeek = "SELECT sum(ELEC)\
                                FROM data\
                                GROUP BY strftime('%Y-%m-%d %W', DateTime)\
                                ORDER BY DateTime DESC\
                                LIMIT 1"
                                
FETCH_ELEC_query_byMonth = "SELECT sum(ELEC)\
                                FROM data\
                                GROUP BY strftime('%Y-%m',DateTime)\
                                ORDER BY DateTime DESC\
                                LIMIT 1"

FETCH_WATER_query = "SELECT avg(TMP), avg(TDS), avg(PH), avg(DO)\
                    FROM data"

hours = [[hour for hour in range(24) if hour%6 == 0],
        [hour for hour in range(24) if hour%6 == 1],
        [hour for hour in range(24) if hour%6 == 2],
        [hour for hour in range(24) if hour%6 == 3],
        [hour for hour in range(24) if hour%6 == 4],
        [hour for hour in range(24) if hour%6 == 5]]

