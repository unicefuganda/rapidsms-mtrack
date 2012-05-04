-- Let's make the DB sweat for our sake!!!
BEGIN;
CREATE OR REPLACE FUNCTION get_anscestors(loc_id INTEGER) RETURNS SETOF locations_location AS
$delim$
     DECLARE
        r locations_location%ROWTYPE;
        our_lft INTEGER;
        our_rght INTEGER;
    BEGIN
        SELECT INTO our_lft lft FROM locations_location WHERE id = loc_id;
        SELECT INTO our_rght rght FROM locations_location WHERE id = loc_id;
        FOR r IN SELECT * FROM locations_location WHERE lft < our_lft AND rght > our_rght
        LOOP
            RETURN NEXT r;
        END LOOP;
        RETURN;
    END;
$delim$ LANGUAGE 'plpgsql';

--CREATE OR REPLACE FUNCTION get_district(loc_id INTEGER) RETURNS SETOF TEXT AS
--$delim$
--     DECLARE
--        r TEXT;
--        our_lft INTEGER;
--        our_rght INTEGER;
--    BEGIN
--        SELECT INTO our_lft lft FROM locations_location WHERE id = loc_id;
--        SELECT INTO our_rght rght FROM locations_location WHERE id = loc_id;
--        FOR r IN SELECT name FROM locations_location WHERE lft < our_lft AND rght > our_rght AND type_id='district'
--        LOOP
--            RETURN NEXT r;
--        END LOOP;
--        RETURN;
--    END;
--$delim$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION get_district(loc_id INTEGER) RETURNS TEXT AS
$delim$
     DECLARE
        r TEXT;
        our_lft INTEGER;
        our_rght INTEGER;
    BEGIN
        SELECT INTO our_lft lft FROM locations_location WHERE id = loc_id;
        SELECT INTO our_rght rght FROM locations_location WHERE id = loc_id;
        FOR r IN SELECT name FROM locations_location WHERE lft <= our_lft AND rght >= our_rght AND type_id='district'
        LOOP
            RETURN r;
        END LOOP;
        RETURN 'None';
    END;
$delim$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION get_location_name(loc_id INTEGER) RETURNS TEXT AS
$delim$
    DECLARE
        xname TEXT;
    BEGIN
        SELECT INTO xname name FROM locations_location WHERE id = loc_id;
        IF xname IS NULL THEN
            RETURN 'None';
        END IF;
        RETURN xname;
    END;
$delim$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION get_contact_facility(contact_id INTEGER) RETURNS TEXT AS
$delim$
    DECLARE
        xname TEXT;
    BEGIN
        SELECT INTO xname a.name || ' ' || b.name
        FROM
            healthmodels_healthfacilitybase a, healthmodels_healthfacilitytypebase b
        WHERE
            a.id =(SELECT facility_id FROM healthmodels_healthproviderbase WHERE contact_ptr_id = contact_id)
            AND a.type_id = b.id;
        IF xname IS NULL THEN
            RETURN 'None';
        END IF;
        RETURN xname;
    END;
$delim$ LANGUAGE 'plpgsql';

--- maintains reports with no facility
DROP VIEW IF EXISTS xform_submissions_view;
CREATE VIEW xform_submissions_view AS
SELECT
    a.id AS report_id, b.name AS report, a.created AS "date",
    d.name AS reporter, d.id AS reporter_id, c.identity AS phone,
    get_district(d.reporting_location_id) as district,
    get_contact_facility(d.id) AS facility,
    CASE WHEN d.village_id IS NOT NULL THEN
        get_location_name(d.village_id)
        --WHEN d.reporting_location_id IS NOT NULL THEN
        --    get_location_name(d.reporting_location_id)
        -- ELSE 'None'
        ELSE ''
    END AS village,
    CASE WHEN a.has_errors IS TRUE THEN 'Yes' ELSE 'No' END AS valid
FROM rapidsms_xforms_xformsubmission a, rapidsms_xforms_xform b, rapidsms_connection c, rapidsms_contact d
WHERE
    a.xform_id = b.id
    AND a.connection_id IS NOT NULL
    AND b.keyword
        IN ('com', 'mal', 'rutf', 'epi', 'home', 'birth', 'muac', 'opd', 'test', 'treat', 'rdt', 'act', 'qun', 'cases', 'death')
    AND (a.connection_id = c.id AND c.contact_id = d.id)
    ORDER BY a.created DESC;

-- for all fields => gives us the attributes /headings
DROP VIEW IF EXISTS xformfields_view;
CREATE VIEW xformfields_view AS
SELECT
    b.name, c.description, c.slug
FROM
    rapidsms_xforms_xformfield a, rapidsms_xforms_xform b, eav_attribute c
WHERE
    a.attribute_ptr_id = c.id AND a.xform_id = b.id
ORDER BY c.slug;

--
DROP VIEW IF EXISTS submissions_values_view;
CREATE VIEW submissions_values_view AS
SELECT
    d.id as submission, b.id AS value_id, a.name, a.slug,
    CASE WHEN a.datatype = 'int' THEN
        ''||b.value_int
    WHEN a.datatype = 'text' THEN
        ''||b.value_text
    WHEN a.datatype = 'float' THEN
        ''||b.value_float
    WHEN a.datatype = 'bool' THEN
        ''||b.value_bool
    WHEN a.datatype = 'date' THEN
        ''||b.value_date
    ELSE ''||0
    END AS value
FROM eav_attribute a, eav_value b, rapidsms_xforms_xformsubmissionvalue c, rapidsms_xforms_xformsubmission d
    WHERE b.attribute_id = a.id AND (b.id = c.value_ptr_id AND (c.submission_id = d.id));

COMMIT;
