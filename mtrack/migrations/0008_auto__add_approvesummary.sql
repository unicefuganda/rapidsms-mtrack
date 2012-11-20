CREATE VIEW reports_view AS
SELECT
    a.id AS report_id, b.name AS report, b.keyword, a.created AS "date",
    d.name AS reporter, d.id AS reporter_id, d.active, c.identity AS phone,
    --get_district(d.reporting_location_id) as district,
    -- get_contact_facility(d.id) AS facility,
    a.has_errors,
    a.approved
FROM rapidsms_xforms_xformsubmission a, rapidsms_xforms_xform b, rapidsms_connection c, rapidsms_contact d
WHERE
    a.xform_id = b.id
    AND a.connection_id IS NOT NULL
    AND b.keyword
        IN ('com', 'mal', 'rutf', 'epi', 'home', 'birth', 'muac', 'opd', 'test', 'treat', 'rdt', 'act', 'qun', 'cases', 'death','doc', 'med')
    AND (a.connection_id = c.id AND c.contact_id = d.id)
    ORDER BY a.created DESC;
