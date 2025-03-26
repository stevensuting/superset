# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from datetime import datetime
from typing import Any, cast

import pandas as pd

from superset import app, config
from superset.common.query_object import QueryObject
from superset.utils.core import FilterOperator, GenericDataType
from superset.utils.date_parser import get_since_until


def get_since_until_from_time_range(
    time_range: str | None = None,
    time_shift: str | None = None,
    extras: dict[str, Any] | None = None,
) -> tuple[datetime | None, datetime | None]:
    return get_since_until(
        relative_start=(extras or {}).get(
            "relative_start", app.config["DEFAULT_RELATIVE_START_TIME"]
        ),
        relative_end=(extras or {}).get(
            "relative_end", app.config["DEFAULT_RELATIVE_END_TIME"]
        ),
        time_range=time_range,
        time_shift=time_shift,
        instant_time_comparison_range=(extras or {}).get(
            "instant_time_comparison_range"
        ),
    )


# pylint: disable=invalid-name
def get_since_until_from_query_object(
    query_object: QueryObject,
) -> tuple[datetime | None, datetime | None]:
    """
    this function will return since and until by tuple if
    1) the time_range is in the query object.
    2) the x-axis column is in the columns field
       and its corresponding `temporal_range` filter is in the adhoc filters.
    :param query_object: a valid query object
    :return: since and until by tuple
    """
    if query_object.time_range:
        return get_since_until_from_time_range(
            time_range=query_object.time_range,
            time_shift=query_object.time_shift,
            extras=query_object.extras,
        )

    time_range = None
    for flt in query_object.filter:
        if flt.get("op") == FilterOperator.TEMPORAL_RANGE.value and isinstance(
            flt.get("val"), str
        ):
            time_range = cast(str, flt.get("val"))

    return get_since_until_from_time_range(
        time_range=time_range,
        time_shift=query_object.time_shift,
        extras=query_object.extras,
    )

def _transform_temporal_columns(df: pd.DataFrame, coltypes: list[GenericDataType]) -> pd.DataFrame:
    """
    Transform temporal columns according to TEMPORAL_COLUMN_FORMAT.
    
    Args:
        df: The DataFrame to transform
        coltypes: List of column data types
        
    Returns:
        DataFrame with transformed temporal columns
    """
    try:
        # Get format from config
        temporal_format = config.TEMPORAL_COLUMN_FORMAT or ''
        if not temporal_format:
            return df  # No transformation if format not specified
        
        # Create a copy to avoid modifying the original
        result_df = df.copy()
        
        # Identify temporal columns
        temporal_indices = [
            i for i, coltype in enumerate(coltypes) 
            if coltype == GenericDataType.TEMPORAL
        ]
        
        if not temporal_indices:
            return df  # No temporal columns to transform
        
        temporal_columns = [df.columns[i] for i in temporal_indices]
        
        # Function to format a single date value
        def format_date(value):
                if pd.isna(value) or (isinstance(value, str) and value in ['-∞', '−∞', '∞']):
                    return value
                
                try:
                    # Ensure value is a pandas Timestamp
                    if not isinstance(value, pd.Timestamp):
                        if isinstance(value, str):
                            value = pd.Timestamp(value)
                        elif isinstance(value, datetime):
                            value = pd.Timestamp(value)
                    
                    # Check if value has time component (non-zero time)
                    has_time = (value.hour != 0 or value.minute != 0 or value.second != 0)
                    
                    # Check if format has time component
                    format_has_time = any(char in temporal_format for char in 'HhmsaSA')
                    
                    # Extract date-only part of the format
                    date_only_format = temporal_format.split('T')[0] if 'T' in temporal_format else temporal_format
                    
                    # Convert moment.js/javascript format to Python strftime format
                    def moment_to_python_format(moment_format):
                        # Create a regex pattern to match moment tokens
                        import re
                        pattern = re.compile(r'(YYYY|YY|MM|M|DD|D|HH|H|hh|h|mm|m|ss|s|SSS|A|a|ddd|dddd|MMM|MMMM|Do|X|Z|ZZ)')
                        
                        # Mapping between moment.js and Python's strftime formats
                        format_map = {
                            'YYYY': '%Y',  # 4-digit year
                            'YY': '%y',    # 2-digit year
                            'MM': '%m',    # month (01-12)
                            'M': '%-m',    # month (1-12) - no leading zero
                            'DD': '%d',    # day of month (01-31)
                            'D': '%-d',    # day of month (1-31) - no leading zero
                            'HH': '%H',    # hours (00-23)
                            'H': '%-H',    # hours (0-23) - no leading zero
                            'hh': '%I',    # hours (01-12)
                            'h': '%-I',    # hours (1-12) - no leading zero
                            'mm': '%M',    # minutes (00-59)
                            'm': '%-M',    # minutes (0-59) - no leading zero
                            'ss': '%S',    # seconds (00-59)
                            's': '%-S',    # seconds (0-59) - no leading zero
                            'SSS': '%f',   # microseconds (truncated to milliseconds)
                            'A': '%p',     # AM/PM
                            'a': '%p',     # am/pm
                            'ddd': '%a',   # abbreviated weekday name
                            'dddd': '%A',  # full weekday name
                            'MMM': '%b',   # abbreviated month name
                            'MMMM': '%B',  # full month name
                            'Do': '%-d',   # day of month with ordinal (Python doesn't support this directly)
                            'X': '%s',     # Unix timestamp
                            'Z': '%z',     # timezone offset
                            'ZZ': '%z',    # timezone offset
                        }
                        
                        # Use regex to find and replace tokens
                        def replace_token(match):
                            token = match.group(0)
                            return format_map.get(token, token)
                            
                        python_format = pattern.sub(replace_token, moment_format)
                        
                        return python_format
                    
                    # Convert formats
                    py_format = moment_to_python_format(temporal_format)
                    py_date_only_format = moment_to_python_format(date_only_format)
                    # Apply formatting logic
                    if has_time and not format_has_time:
                        # If value has time but format doesn't, format date and add time
                        date_part = value.strftime(py_date_only_format)
                        time_part = value.strftime('T%H:%M:%S')
                        return f"{date_part}{time_part}"
                    elif not has_time and format_has_time:
                        # If value doesn't have time but format does, format date only
                        return value.strftime(py_date_only_format)
                    else:
                        # Both have time or both don't have time
                        return value.strftime(py_format)
                except Exception as e:
                    # Return original value if any error occurs
                    return value
        
        # Apply transformation to each temporal column
        for col in temporal_columns:
            result_df[col] = result_df[col].apply(format_date)
        
        return result_df
    except:
        # If any error occurs in the transformation process, return original DataFrame
        return df