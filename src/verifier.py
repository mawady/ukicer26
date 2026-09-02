from models import ModuleInput, ModuleSpecification


class ConsistencyVerifier:
    def __init__(self, hours_per_cats=10):
        self.hours_per_cats = hours_per_cats

    def verify(self, module_input: ModuleInput, spec: ModuleSpecification):
        checks = []

        expected_hours = module_input.cats * self.hours_per_cats
        actual_hours = (
            spec.total_scheduled_hours
            + spec.total_independent_hours
            + spec.total_placement_hours
        )

        checks.append({
            "name": "Credit-to-learning-hours consistency",
            "passed": abs(expected_hours - actual_hours) <= max(1, expected_hours * 0.05),
            "expected": expected_hours,
            "actual": actual_hours,
            "message": f"Expected approx {expected_hours} total hours, found {actual_hours}."
        })

        # Calculate weighting exclusively for summative assessments
        summative_weight = sum(
            a.weighting for a in spec.assessments 
            if a.type.lower() == "summative"
        )
        checks.append({
            "name": "Assessment weighting (Summative)",
            "passed": abs(summative_weight - 100) < 0.01,
            "expected": 100,
            "actual": summative_weight,
            "message": f"Summative assessment weighting totals {summative_weight}% (must equal 100%). Formative assessments carry 0% weight."
        })

        ilo_codes = {ilo.code for ilo in module_input.ilos}
        syllabus_ilos = {
            ilo for week in spec.syllabus for ilo in week.ilo_mapping
        }
        assessment_ilos = {
            ilo for assessment in spec.assessments for ilo in assessment.mapped_ilos
        }

        missing_syllabus = ilo_codes - syllabus_ilos
        missing_assessment = ilo_codes - assessment_ilos

        checks.append({
            "name": "ILO coverage in syllabus",
            "passed": not missing_syllabus,
            "missing": list(missing_syllabus),
            "message": "All ILOs covered in syllabus."
                if not missing_syllabus else f"Missing ILOs in syllabus: {sorted(missing_syllabus)}"
        })

        checks.append({
            "name": "ILO coverage in assessment",
            "passed": not missing_assessment,
            "missing": list(missing_assessment),
            "message": "All ILOs covered in assessments."
                if not missing_assessment else f"Missing ILOs in assessments: {sorted(missing_assessment)}"
        })

        checks.append({
            "name": "Syllabus progression",
            "passed": len(spec.syllabus) >= 1,
            "message": f"{len(spec.syllabus)} teaching weeks generated."
        })

        return checks

    @staticmethod
    def failed_checks(checks):
        return [c["message"] for c in checks if not c.get("passed")]