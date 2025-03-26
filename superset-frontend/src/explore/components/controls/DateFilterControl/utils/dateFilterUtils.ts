/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import {
  NO_TIME_RANGE,
  JsonObject,
  customTimeRangeDecode,
} from '@superset-ui/core';
import { useSelector } from 'react-redux';
import moment from 'moment';
import getBootstrapData from 'src/utils/getBootstrapData';
import {
  COMMON_RANGE_VALUES_SET,
  CALENDAR_RANGE_VALUES_SET,
  CURRENT_RANGE_VALUES_SET,
} from '.';
import { FrameType } from '../types';

export const guessFrame = (timeRange: string): FrameType => {
  if (COMMON_RANGE_VALUES_SET.has(timeRange)) {
    return 'Common';
  }
  if (CALENDAR_RANGE_VALUES_SET.has(timeRange)) {
    return 'Calendar';
  }
  if (CURRENT_RANGE_VALUES_SET.has(timeRange)) {
    return 'Current';
  }
  if (timeRange === NO_TIME_RANGE) {
    return 'No filter';
  }
  if (customTimeRangeDecode(timeRange).matchedFlag) {
    return 'Custom';
  }
  return 'Advanced';
};

export function useDefaultTimeFilter() {
  return (
    useSelector(
      (state: JsonObject) => state?.common?.conf?.DEFAULT_TIME_FILTER,
    ) ?? NO_TIME_RANGE
  );
}

/**
 * Formats a timerange string according to the specified date/time format using moment.js
 * @param timerangeValue - The timerange string in format like "2025-03-19 ≤ col < 2025-03-26"
 * @param format - The desired output format (e.g., 'YYYY-MM-DD', 'YYYY-MM-DDTHH:mm:ss')
 * @returns A string with formatted timerange using the original separators
 */
export function formatTimerange(timerangeValue: string): string {
  // Extract the dates and separators using regex
  const format = getBootstrapData()?.common?.TEMPORAL_COLUMN_FORMAT;
  if (!format) {
    return timerangeValue;
  }
  const regex =
    /((?:\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2})?)|[-−]∞) (≤) ([a-zA-Z0-9_]+) (<) ((?:\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2})?)|∞)/;
  const match = timerangeValue.match(regex);

  if (!match) {
    return timerangeValue;
  }

  const startDateStr = match[1];
  const lte = match[2]; // ≤ symbol
  const columnName = match[3]; // column name
  const lt = match[4]; // < symbol
  const endDateStr = match[5];

  // Create moment objects
  const startMoment = moment(startDateStr);
  const endMoment = moment(endDateStr);

  if (!startMoment.isValid() || !endMoment.isValid()) {
    return timerangeValue;
  }

  // Determine if input has time component
  const startHasTime = startDateStr.includes('T');
  const endHasTime = endDateStr.includes('T');

  // Determine if format includes time components
  const formatHasTime =
    format.includes('H') ||
    format.includes('h') ||
    format.includes('m') ||
    format.includes('s') ||
    format.includes('S') ||
    format.includes('A') ||
    format.includes('a');

  // Extract the date-only part of the format
  const dateOnlyFormat = format.split('T')[0];

  // Process startDate based on requirements
  let formattedStartDate: string;
  if (startHasTime && !formatHasTime) {
    // If starttime has time and output format doesn't, change date as per format and add time
    const formattedDate = startMoment.format(dateOnlyFormat);
    const timeComponent = startMoment.format('THH:mm:ss');
    formattedStartDate = `${formattedDate}${timeComponent}`;
  } else if (!startHasTime && formatHasTime) {
    // If starttime doesn't have time and output format does, change date as per format and don't add time
    formattedStartDate = startMoment.format(dateOnlyFormat);
  } else {
    // If starttime and format both have time or both don't have time, use format as is
    formattedStartDate = startMoment.format(format);
  }

  // Process endDate based on requirements
  let formattedEndDate: string;
  if (endHasTime && !formatHasTime) {
    // If endtime has time and output format doesn't, change date as per format and add time
    const formattedDate = endMoment.format(dateOnlyFormat);
    const timeComponent = endMoment.format('THH:mm:ss');
    formattedEndDate = `${formattedDate}${timeComponent}`;
  } else if (!endHasTime && formatHasTime) {
    // If endtime doesn't have time and output format does, change date as per format and don't add time
    formattedEndDate = endMoment.format(dateOnlyFormat);
  } else {
    // If endtime and format both have time or both don't have time, use format as is
    formattedEndDate = endMoment.format(format);
  }

  // Reassemble the timerange string with original separators
  return `${formattedStartDate} ${lte} ${columnName} ${lt} ${formattedEndDate}`;
}

export function formatSingleDate(dateValue: string): string {
  try {
    // Get format from bootstrap data
    const format = getBootstrapData()?.common?.TEMPORAL_COLUMN_FORMAT;
    if (!format) {
      return dateValue;
    }
    // Handle non-date values
    if (dateValue === '-∞' || dateValue === '−∞' || dateValue === '∞') {
      return dateValue;
    }

    // Create moment object
    const dateMoment = moment(dateValue);

    if (!dateMoment.isValid()) {
      return dateValue; // Return original value if date is invalid
    }

    // Determine if input has time component
    const hasTime = dateValue.includes('T');

    // Determine if format includes time components
    const formatHasTime =
      format.includes('H') ||
      format.includes('h') ||
      format.includes('m') ||
      format.includes('s') ||
      format.includes('S') ||
      format.includes('A') ||
      format.includes('a');

    // Extract the date-only part of the format
    const dateOnlyFormat = format.split('T')[0];

    // Apply the same formatting logic as in the range function
    let formattedDate: string;
    if (hasTime && !formatHasTime) {
      // If input has time and output format doesn't, change date as per format and add time
      const formattedDatePart = dateMoment.format(dateOnlyFormat);
      const timeComponent = dateMoment.format('THH:mm:ss');
      formattedDate = `${formattedDatePart}${timeComponent}`;
    } else if (!hasTime && formatHasTime) {
      // If input doesn't have time and output format does, change date as per format and don't add time
      formattedDate = dateMoment.format(dateOnlyFormat);
    } else {
      // If both input and format have time or both don't have time, use format as is
      formattedDate = dateMoment.format(format);
    }

    return formattedDate;
  } catch (error) {
    // If any error occurs during processing, return the original input
    return dateValue;
  }
}
