import streamlit as st
import pandas as pd
import re
from rapidfuzz import fuzz

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
        "Training"
    ],

    "Blind CRC": [
        "Data Privacy",
        "Training"
    ],

    "CRC": [
        "Data Privacy",
        "Training"
    ],

    "CRC Main": [
        "Data Privacy",
        "Training"
    ],

    "Main CRC": [
        "Data Privacy",
        "Training"
    ],

    "Injection nurse": [
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

    text = str(text).lower()

    text = re.sub(r"[-,.]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def compact_name(text):
    text = normalize_name(text)
    return text.replace(" ", "")


def generate_name_variants(name):

    name = normalize_name(name)

    tokens = name.split()

    variants = set()

    variants.add(name)
    variants.add("".join(tokens))

    if len(tokens) >= 2:

        variants.add(
            " ".join(reversed(tokens))
        )

        variants.add(
            "".join(reversed(tokens))
        )

    # 한국 이름 대응
    if len(tokens) == 3:

        first = tokens[0]
        middle = tokens[1]
        last = tokens[2]

        # Ji Young Yoon
        variants.add(last + first + middle)
        variants.add(last + middle + first)

        variants.add(
            f"{last} {first}{middle}"
        )

        variants.add(
            f"{last} {first} {middle}"
        )

    return variants


def investigator_match(name, description):

    desc = compact_name(description)

    variants = generate_name_variants(name)

    for v in variants:

        v_compact = compact_name(v)

        if v_compact in desc:
            return True

        score = fuzz.partial_ratio(
            v_compact,
            desc
        )

        if score >= 85:
            return True

    return False


def best_match_score(description, contact_names):

    best_name = ""
    best_score = 0

    desc = compact_name(description)

    for staff_name in contact_names:

        variants = generate_name_variants(staff_name)

        score = max(
            fuzz.partial_ratio(
                compact_name(v),
                desc
            )
            for v in variants
        )

        if score > best_score:
            best_score = score
            best_name = staff_name

    return best_name, best_score

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

    st.success(
        f"Artifact Uploaded ({len(df)} records)"
    )


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

    st.success(
        f"Contact List Uploaded ({len(contact_df)} staff)"
    )

    # ===================================
    # Internal Matching data
    # ===================================
    staff_results = []

    for name in contact_df["Name(EN)"]:

        docs_found = []

        for _, row in staff_docs.iterrows():

            if investigator_match(
                name,
                row["Description"]
            ):
                docs_found.append(
                    row["Classification"]
                )

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
    # Training Data
    # ======================================

    training_records = []

    for name in contact_df["Name(EN)"]:

        role = contact_df.loc[
            contact_df["Name(EN)"] == name,
            "Role"
        ].iloc[0]

        for _, row in staff_docs.iterrows():

            if "training" not in str(
                row["Classification"]
            ).lower():

                continue

            matched = investigator_match(
                name,
                row["Description"]
            )

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

    training_df = pd.DataFrame(
        training_records
    )

    st.write(training_df.head())

    # ======================================
    # Unmatched Documents
    # ======================================

    st.subheader("Unmatched Documents")

    unmatched_docs = []

    for _, row in staff_docs.iterrows():

        matched = False

        for staff_name in contact_df["Name(EN)"]:

            if investigator_match(
                staff_name,
                row["Description"]
            ):
                matched = True
                break

        if not matched:

            best_name, best_score = best_match_score(
                row["Description"],
                contact_df["Name(EN)"]
            )

            unmatched_docs.append(
                {
                    "Document Date":
                        pd.to_datetime(
                            row["Document Date"]
                        ).strftime("%Y-%m-%d"),

                    "Classification":
                        row["Classification"],

                    "Description":
                        row["Description"],

                    "Closest staff":
                        best_name,

                    "Match Score":
                        round(best_score,1)

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

# ======================================
# Main Dashboard
# ======================================

    # Role Filter
    role_list = sorted(
        contact_df["Role"].dropna().unique()
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        selected_role = st.selectbox(
            "Select Role",
            ["All"] + role_list
        )

    with col2:
        search_name = st.text_input(
            "Search Staff Name"
        )

    dashboard_df = compliance_df.copy()

    # Role Filter 적용
    if selected_role != "All":
        dashboard_df = dashboard_df[
            dashboard_df["Role"] == selected_role
        ]

    # name filter 적용
    if search_name:
        dashboard_df = dashboard_df[
            dashboard_df["Name"].str.contains(
                search_name,
                case=False,
                na=False
            )
        ]
    st.metric(
        "Displayed Staff",
        len(dashboard_df)
    )
    # 요약 테이블 > 별로면 삭제 예정
    
    summary_df = dashboard_df.copy()

    summary_df = summary_df[
        [
            "Name",
            "Role",
            "Curriculum Vitae",
            "Financial Disclosure",
            "Data Privacy",
            "Training"
        ]
    ]

    st.dataframe(
        summary_df,
        use_container_width=True
    )

    for _, person in dashboard_df.iterrows():

        staff_name = person["Name"]
        role = person["Role"]

        person_training = training_df[
            training_df["Name"] == staff_name
        ]

        completed = 0
        required = 0

        for doc in [
            "Curriculum Vitae",
            "Financial Disclosure",
            "Data Privacy",
            "Training"
        ]:

            if person[doc] != "-":

                required += 1

                if person[doc] == "✅":
                    completed += 1

        score = round(
            completed / required * 100
        ) if required > 0 else 0

        if score == 100:
            status = "🟢"

        elif score >= 75:
            status = "🟡"

        else:
            status = "🔴"

        with st.expander(
            f"{status} {staff_name} | {role} | Compliance {score}%"
        ):

            st.markdown("### Document Status")

            doc_status_df = pd.DataFrame(
                {
                    "Document": [
                        "Curriculum Vitae",
                        "Financial Disclosure",
                        "Data Privacy",
                        "Training"
                    ],
                    "Status": [
                        person["Curriculum Vitae"],
                        person["Financial Disclosure"],
                        person["Data Privacy"],
                        person["Training"]
                    ]
                }
            )

            st.dataframe(
                doc_status_df,
                use_container_width=True
            )

            st.markdown("### Training Records")

            if len(person_training) > 0:

                st.dataframe(
                    person_training[
                        [
                            "Training Description",
                            "Date"
                        ]
                    ],
                    use_container_width=True
                )

            else:

                st.warning(
                    "No training records found."
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
