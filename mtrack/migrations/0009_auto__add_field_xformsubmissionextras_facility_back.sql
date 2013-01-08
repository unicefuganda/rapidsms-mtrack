CREATE OR REPLACE FUNCTION update_facility_extras() RETURNS TRIGGER AS $update_facility_extras$
    DECLARE
    f INTEGER;
    hp INTEGER;
    BEGIN
        IF TG_OP = 'DELETE' THEN
            SELECT contact_id INTO hp FROM rapidsms_connection WHERE id = OLD.connection_id;
            -- update total reports for health providers
            UPDATE healthmodels_healthproviderextras SET total_reports = total_reports - 1
                WHERE health_provider_id = hp;
            IF OLD.has_errors = FALSE THEN
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reports = total_reports - 1
                    WHERE health_facility_id = f;
                END IF;
            END IF;
            RETURN OLD;
        END IF;
        SELECT contact_id INTO hp FROM rapidsms_connection WHERE id = NEW.connection_id;
        IF hp IS NULL THEN
            RETURN NULL;
        END IF;
        IF TG_OP = 'INSERT'  THEN -- insert or update
            -- update total reports for health providers
            UPDATE healthmodels_healthproviderextras SET total_reports = total_reports + 1
                WHERE health_provider_id = hp;
            IF NEW.has_errors = FALSE AND NEW.connection_id IS NOT NULL THEN
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reports = total_reports + 1
                    WHERE health_facility_id = f;
                END IF;
            END IF;
            RETURN NEW;
        ELSIF TG_OP = 'UPDATE' THEN
            IF NEW.has_errors = OLD.has_errors THEN
                RETURN NEW;
            END IF;
            IF NEW.has_errors = FALSE AND OLD.has_errors = TRUE THEN
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reports = total_reports + 1
                    WHERE health_facility_id = f;
                END IF;
                RETURN NEW;
            ELSIF NEW.has_errors = TRUE AND OLD.has_errors = FALSE THEN
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reports = total_reports - 1
                    WHERE health_facility_id = f;
                END IF;
                RETURN NEW;
            END IF;
            RETURN NEW;
        END IF;
    END;
$update_facility_extras$ LANGUAGE plpgsql;
