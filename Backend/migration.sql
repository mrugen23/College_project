-- Migration update script to add budget_id to existing expenses table
ALTER TABLE expenses ADD COLUMN budget_id INT NULL;
ALTER TABLE expenses ADD CONSTRAINT fk_budget FOREIGN KEY (budget_id) REFERENCES budgets(id) ON DELETE SET NULL; 