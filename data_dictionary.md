# Data Dictionary

## 1. School Master
| Original Field | Cleaned Field | Transformation | Data Type |
|---|---|---|---|
| `school_id` | `school_id_clean` | Removed dashes/spaces, extracted numbers, padded to SCH0000 format. | String |
| `school_name` | `school_name` | Unchanged | String |
| `district` | `district` | Unchanged | String |

## 2. Attendance
| Original Field | Cleaned Field | Transformation | Data Type |
|---|---|---|---|
| `school_id` | `school_id_clean` | Standardized ID | String |
| `date` | `date_clean` | Converted to Datetime using pandas | Date |
| N/A | `is_proxy_attendance` | Flagged TRUE if Sunday & present_students == total_students | Boolean |
| N/A | `impossible_attendance` | Flagged TRUE if present_students > total_students | Boolean |

## 3. Infrastructure
| Original Field | Cleaned Field | Transformation | Data Type |
|---|---|---|---|
| `has_electricity` | `has_electricity_clean` | Mapped Yes/1/Hai to True, No/0/Nahi to False | Boolean |
| `has_drinking_water` | `has_drinking_water_clean` | Same boolean map | Boolean |
| N/A | `infrastructure_deficit_index` | Calculated as (Missing Amenities / Total Tracked) | Float |

## 4. Mid-Day Meal (MDM)
| Original Field | Cleaned Field | Transformation | Data Type |
|---|---|---|---|
| `Vendor Name` | `vendor_clean` | Lowercase, stripped punctuation, Title case | String |
| `Grain` | `grain_clean` | Mapped 'chawal' -> 'Rice', 'gehu' -> 'Wheat' | String |
| `Quantity` | `qty_kg_clean` | Extracted float. Converted grams/bags to KG (1 Bag = 50KG) | Float |
| `Cost` | `cost_clean` | Removed ₹, Rs, commas | Float |

## 5. Test Scores
| Original Field | Cleaned Field | Transformation | Data Type |
|---|---|---|---|
| `avg_score`, `grading_scale` | `score_percentage_clean` | Converted Letter Grades, CGPAs, Raw marks, and Pct to unified 0-100 scale. | Float |
