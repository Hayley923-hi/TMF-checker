import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
from itertools import permutations

required_docs = {

    "PI": [
        "Curriculum Vitae",
        "Financial Disclosure",
        "Data Privacy",
        "Training"
    ],

    "Sub-I": [
        "Curriculum Vitae",
        "Financial Disclosure",
        "Data Privacy"
    ],

    "Blind CRC": [
        "Data Privacy",
        "Training"
    ],

    "CRC": [
        "Data Privacy",
        "Training"
    ],

    "Study Nurse": [
        "Data Privacy",
        "Training"
    ],

    "SC": [
        "Data Privacy",
        "Training"
    ],

    "main SC": [
        "Data Privacy",
        "Training"
    ],

    "backup SC": [
        "Data Privacy",
        "Training"
    ],

    "Unblind CRC": [
        "Data Privacy",
        "Training"
    ],

    "Lab technician": [
        "Data Privacy",
        "Training"
    ],

    "Pharmacist": [
        "Data Privacy",
        "Training"
    ],

    "UB Pharmacist": [
        "Data Privacy",
        "Training"
    ],

    "UB Main Pharmacist": [
        "Data Privacy",
        "Training"
    ]
}


def normalize_name(text):

    return (
        str(text)
        .replace(",", "")
        .replace("-", "")
        .replace(" ", "")
        .lower()
    )


def generate_name_variations(name):

    cleaned = str(name).replace(",", " ")
    parts = cleaned.split()

    variations = set()

    for p in permutations(parts):

        variations.add(
            normalize_name(
                "".join(p)
            )
        )

    return list(variations)


# ==================================================
# Artifact upload
# ==================================================


st.title("TMF Compliance Checker")

uploaded_file = st.file_uploader(
    "Artifact Excel Upload",
    type=["xlsx"]
)

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    st.success("File Uploaded Successfully!")

    st.dataframe(df.head())

# ==================================================
# Document Type Summary
# ==================================================
st.subheader("Document Type Summary")

if uploaded_file:

    classification_col = df["Classification"]

    dpa_count = classification_col.str.contains(
        "Data Privacy",
        case=False,
        na=False
    ).sum()

    cv_count = classification_col.str.contains(
        "Curriculum Vitae",
        case=False,
        na=False
    ).sum()

    fdf_count = classification_col.str.contains(
        "Financial Disclosure",
        case=False,
        na=False
    ).sum()

    training_count = classification_col.str.contains(
        "Training",
        case=False,
        na=False
    ).sum()

    st.write(f"DPA: {dpa_count}")
    st.write(f"CV: {cv_count}")
    st.write(f"FDF: {fdf_count}")
    st.write(f"Training: {training_count}")

    staff_docs = df[
        df["Classification"].str.contains(
            "Data Privacy|Curriculum Vitae|Financial Disclosure|Training",
            case=False,
            na=False
        )
    ]
# ==================================================
# Contact List upload
# ==================================================
contact_file = st.file_uploader(
    "Contact List Upload",
    type=["xlsx"]
)

if contact_file and uploaded_file:

    contact_df = pd.read_excel(contact_file)

    # Role 공백 제거
    contact_df["Role"] = (
        contact_df["Role"]
        .astype(str)
        .str.strip()
    )

    contact_df["Name(EN)"] = (
        contact_df["Name(EN)"]
        .astype(str)
        .str.strip()
    )

    st.success("Contact List Uploaded!")

    st.dataframe(contact_df.head())

    # ===================================
    # Internal Matching data
    # ===================================
    staff_results = []

    name_col = "Name(EN)"

    for name in contact_df["Name(EN)"]:

        search_names = generate_name_variations(name)

        docs_found = []

        for _, row in staff_docs.iterrows():

            desc_clean = normalize_name(
                str(row["Description"])
            )

            for candidate in search_names:

                if candidate in desc_clean:
                    docs_found.append(
                        row["Classification"]
                    )
                    break

                score = fuzz.partial_ratio(
                    candidate,
                    desc_clean
                )

                if score >= 75:
                    docs_found.append(
                        row["Classification"]
                    )
                    break

        docs_found = list(set(docs_found))

        staff_results.append(
            {
                "Name": name,
                "Documents": ", ".join(docs_found)
            }
        )

    staff_detail_df = pd.DataFrame(
        staff_results
    )

    # ======================================
    # Unmatched Documents
    # ======================================

    st.subheader("Unmatched Documents")

    all_staff_names = set()

    for name in contact_df["Name(EN)"]:

        variations = generate_name_variations(name)

        for v in variations:
            all_staff_names.add(v)

    unmatched_docs = []

    for _, row in staff_docs.iterrows():

        desc_clean = normalize_name(
         str(row["Description"])
        )

        matched = False

        for staff_name in all_staff_names:

            if staff_name in desc_clean:
                matched = True
                break

            score = fuzz.partial_ratio(
                staff_name,
                desc_clean
            )

            if score >= 75:
                matched = True
                break

        if not matched:

            unmatched_docs.append(
                {
                    "Classification":
                        row["Classification"],
                    "Description":
                        row["Description"],
                    "Document Date":
                        row["Document Date"]
                }
            )

    unmatched_df = pd.DataFrame(
        unmatched_docs
    )

    st.metric(
        "Unmatched Documents",
        len(unmatched_df)
    )

    st.dataframe(
        unmatched_df,
        use_container_width=True
    )

# ======================================
# training detail table
# =======================================
    st.subheader("Training Details")

    training_records = []

    for name in contact_df["Name(EN)"]:

        role = contact_df.loc[
            contact_df["Name(EN)"] == name,
            "Role"
        ].iloc[0]

        search_names = generate_name_variations(name)

        for _, row in staff_docs.iterrows():

            if "training" not in str(
                row["Classification"]
            ).lower():

                continue

            desc_clean = normalize_name(
                str(row["Description"])
            )

            matched = False

            for candidate in search_names:

                score = fuzz.partial_ratio(
                    candidate,
                    desc_clean
                )

                if score >= 85:

                    matched = True

                    break

            if matched:

                training_records.append(
                    {
                        "Name": name,
                        "Role": role,
                        "Training Description":
                            row["Description"],
                        "Date":
                            row["Document Date"]
                    }
                )

    st.write("Training records count:", len(training_records))

    training_df = pd.DataFrame(
        training_records
    )

    st.dataframe(
        training_df,
        use_container_width=True
    )

# ==================================================
# staff summary
# ==================================================
    st.subheader("Staff Summary")

    st.write(f"Total Staff: {len(contact_df)}")

    role_summary = (
        contact_df["Role"]
        .value_counts()
        .reset_index()
    )

    role_summary.columns = ["Role", "Count"]

    st.dataframe(role_summary)

# ==========================================
# Compliance Matrix
# ==========================================

    st.subheader("Compliance Matrix")

    compliance_results = []

    doc_types = [
        "Curriculum Vitae",
        "Financial Disclosure",
        "Data Privacy",
        "Training"
    ]

    for _, person in contact_df.iterrows():

        name = person["Name(EN)"]
        role = person["Role"]

        docs_text = staff_detail_df[
            staff_detail_df["Name"] == name
        ]["Documents"].values[0]

        row = {
            "Name": name,
            "Role": role
        }

        for doc in doc_types:

            needed = (
                role in required_docs
                and doc in required_docs[role]
            )

            found = (
                doc.lower()
                in docs_text.lower()
            )

            if needed:

                if found:
                    row[doc] = "✅"
                else:
                    row[doc] = "❌"

            else:
                row[doc] = "-"

        compliance_results.append(row)

    compliance_df = pd.DataFrame(
        compliance_results
    )
# ==========================================
# Main Dashboard
# ==========================================

    dashboard_results = []

    for _, row in compliance_df.iterrows():

        required = 0
        completed = 0

        for doc in [
            "Curriculum Vitae",
            "Financial Disclosure",
            "Data Privacy",
            "Training"
        ]:

            if row[doc] != "-":

                required += 1

                if row[doc] == "✅":
                    completed += 1

        score = round(
            completed / required * 100
        ) if required > 0 else 0

        if score == 100:
            status = "🟢 Green"

        elif score >= 75:
            status = "🟡 Amber"

        else:
            status = "🔴 Red"

        dashboard_results.append(
            {
                "Site Staff": row["Name"],
                "Role": row["Role"],
                "Compliance Score": f"{score}%",
                "Status": status
            }
        )

    dashboard_df = pd.DataFrame(
        dashboard_results
    )

    st.subheader("Main Dashboard")

    st.dataframe(
        dashboard_df,
        use_container_width=True
    )


# ==========================================
# TMF Health Score
# ==========================================

    required_count = 0
    completed_count = 0

    for _, row in compliance_df.iterrows():

        for doc in [
            "Curriculum Vitae",
            "Financial Disclosure",
            "Data Privacy",
            "Training"
        ]:

            if row[doc] != "-":

                required_count += 1

                if row[doc] == "✅":
                    completed_count += 1

    health_score = round(
        completed_count / required_count * 100,
        1
    )

    st.subheader("TMF Health Score")

    st.metric(
        "Overall TMF Compliance",
        f"{health_score}%"
    )

    # ==================================
    # missing summary 
    # ===================================
    st.subheader("Missing Documents Summary")

    missing_summary = pd.DataFrame({
        "Document": [
            "CV",
            "FDF",
            "DPA",
            "Training"
        ],

        "Missing": [
            (compliance_df["Curriculum Vitae"] == "❌").sum(),
            (compliance_df["Financial Disclosure"] == "❌").sum(),
            (compliance_df["Data Privacy"] == "❌").sum(),
            (compliance_df["Training"] == "❌").sum()
        ]
    })

    st.dataframe(
        missing_summary,
        use_container_width=True
    )

    # ==========================================
    # Missing Only Filter
    # ==========================================

    show_missing_only = st.checkbox(
        "Show Missing Documents Only"
    )

    filtered_df = compliance_df.copy()

    if show_missing_only:

        filtered_df = compliance_df[
            (compliance_df["Curriculum Vitae"] == "❌")
            |
            (compliance_df["Financial Disclosure"] == "❌")
            |
            (compliance_df["Data Privacy"] == "❌")
            |
            (compliance_df["Training"] == "❌")
        ]

    st.metric(
        "Staff With Missing Documents",
        len(
            filtered_df[
                (filtered_df["Curriculum Vitae"] == "❌")
                |
                (filtered_df["Financial Disclosure"] == "❌")
                |
                (filtered_df["Data Privacy"] == "❌")
                |
                (filtered_df["Training"] == "❌")
            ]
        )
    )

    st.dataframe(
        filtered_df,
        use_container_width=True
    )
