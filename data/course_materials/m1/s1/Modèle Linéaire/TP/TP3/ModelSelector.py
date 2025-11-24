from patsy import ModelDesc
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

class ForwardModelSelector:
    """
    A class used to perform forward model selection based on BIC, AIC, and adjusted R-squared criteria.
    Attributes
    ----------
    formula : str
        The formula specifying the model.
    dataset : pandas.DataFrame
        The dataset containing the variables in the formula.
    results : pandas.DataFrame
        A DataFrame to store the results of the forward selection process.
    desc : ModelDesc
        A description of the model derived from the formula.
    covariates : list
        A list of covariate names from the formula.
    response : str
        The name of the response variable from the formula.
    p : int
        The number of covariates.
    compute : bool
        A flag indicating whether the fit method has been called.
    Methods
    -------
    fit():
        Performs forward selection to find the best model based on BIC, AIC, and adjusted R-squared.
    rhs_best_model(criterion='BIC'):
        Returns the right-hand side of the best model formula based on the specified criterion.
    best_model(criterion='BIC'):
        Fits and prints the summary of the best model based on the specified criterion.
    """
    def __init__(self, formula, dataset):
        """
        Initializes an instance of the class with a formula and a dataset.

        Args:
            formula (str): The formula describing the linear model.
            dataset (pandas.DataFrame): The dataset used to fit the model.

        Attributes:
            formula (str): The formula describing the linear model.
            dataset (pandas.DataFrame): The dataset used to fit the model.
            results (pandas.DataFrame): A DataFrame containing the results of the forward selection.
            desc (ModelDesc): A description of the model derived from the formula.
            covariates (list): A list of the names of the covariates in the model.
            response (str): The name of the response variable in the model.
            p (int): The number of covariates in the model.
            compute (bool): A flag indicating whether the fit method has been called.
        """
        self.formula = formula
        self.dataset = dataset
        self.desc = ModelDesc.from_formula(self.formula)
        self.covariates = [term.name() for term in self.desc.rhs_termlist if term.name() != 'Intercept']
        self.response = self.desc.lhs_termlist[0].name()
        self.p = len(self.covariates)
        self.compute = False
        self.results = pd.DataFrame({x: np.zeros(self.p+1).astype(bool) for x in self.covariates})
        self.results['BIC'] = np.zeros(self.p+1)
        self.results['AIC'] = np.zeros(self.p+1)
        self.results['R2_adj'] = np.zeros(self.p+1)

    def fit(self):
        """
        Fits a linear regression model using stepwise selection based on BIC, AIC, and adjusted R-squared.

        This method performs stepwise selection to identify the best set of covariates for the linear regression model.
        It starts with an intercept-only model and iteratively adds covariates that improve the model according to 
        adjusted R-squared, BIC, and AIC criteria.

        Attributes:
        -----------
        self.response : str
            The name of the response variable.
        self.dataset : pandas.DataFrame
            The dataset containing the response and covariates.
        self.results : pandas.DataFrame
            A DataFrame to store the results of the model fitting process.
        self.compute : bool
            A flag indicating whether the model fitting process has been completed.

        Parameters:
        -----------
        None

        Returns:
        --------
        None

        Notes:
        ------
        - The method updates the `self.results` DataFrame with the BIC, AIC, and adjusted R-squared values for each step.
        - The `self.compute` attribute is set to True upon completion.
        """
        model = smf.ols(formula=self.response + ' ~ 1', data=self.dataset).fit()
        selected_covariates = []
        remaining_covariates = self.covariates.copy()
        self.results.loc[0, 'BIC'] = model.bic
        self.results.loc[0, 'AIC'] = model.aic
        self.results.loc[0, 'R2_adj'] = model.rsquared_adj

        for i in range(self.p):
            r2s = {x: 0 for x in remaining_covariates}
            bics = {x: 0 for x in remaining_covariates}
            aics = {x: 0 for x in remaining_covariates}
            r2adjs = {x: 0 for x in remaining_covariates}
            for covariate in remaining_covariates:
                model = smf.ols(formula=self.response + ' ~ ' + '+'.join(selected_covariates + [covariate]), \
                                data=self.dataset).fit()
                r2s[covariate] = model.rsquared
                bics[covariate] = model.bic
                aics[covariate] = model.aic
                r2adjs[covariate] = model.rsquared_adj
            best_covariate = max(r2s, key=r2s.get)
            self.results.loc[i+1, best_covariate] = True
            for covariate in selected_covariates:
                self.results.loc[i+1, covariate] = True
            self.results.loc[i+1, 'BIC'] = bics[best_covariate]
            self.results.loc[i+1, 'AIC'] = aics[best_covariate]
            self.results.loc[i+1, 'R2_adj'] = r2adjs[best_covariate]
            selected_covariates.append(best_covariate)
            remaining_covariates.remove(best_covariate)
        self.compute = True
        return self

    def rhs_best_model(self, criterion='BIC'):
        """
        Selects the best model based on the specified criterion.

        Parameters:
        -----------
        criterion : str, optional
            The criterion to use for model selection. Must be one of 'BIC' (default), 'AIC', or 'R2_adj'.

        Returns:
        --------
        str
            A string representing the best model's covariates joined by ' + ' to help build the formula.

        Raises:
        -------
        ValueError
            If the model has not been fitted yet (self.compute is False).
            If the specified criterion is not one of 'BIC', 'AIC', or 'R2_adj'.

        Notes:
        ------
        - If 'R2_adj' is chosen as the criterion, the model with the maximum adjusted R-squared is selected.
        - For 'BIC' and 'AIC', the model with the minimum value is selected.
        """
        if not self.compute:
            raise ValueError('You must first fit the model using the fit() method')
        if criterion not in ['BIC', 'AIC', 'R2_adj']:
            raise ValueError('The criterion must be BIC, AIC, or R2_adj')
        if criterion == 'R2_adj':
            ind = np.argmax(self.results[criterion])
        else:
            ind = np.argmin(self.results[criterion])
        covariates = [x for x in self.results.columns[:-3] if self.results.loc[ind, x]]
        return ' + '.join(covariates)
    
    def best_model(self, criterion='BIC'):
        """
        Selects and fits the best model based on the specified information criterion.

        Parameters:
        criterion (str): The information criterion to use for model selection. 
                         Options are 'BIC' (default)'BIC', 'AIC', or 'R2_adj'.

        Returns:
        statsmodels.regression.linear_model.RegressionResultsWrapper: The OLS model to be fitted.

        Prints:
        Summary of the fitted OLS model.
        """
        rhs = self.rhs_best_model(criterion)
        mod = smf.ols(formula=self.response + ' ~ ' + rhs, data=self.dataset)
        return mod
