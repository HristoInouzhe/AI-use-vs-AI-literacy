
library(readxl)
library(psych)

options(scipen=999)

# Specify the file path (change this to the path on your computer)
file_path <- "Enter your file path here"

# Read the data from Sheet1
data <- read_excel(file_path, sheet = "Sheet1")

# Display the first few rows of the data
head(data)

summary(data$`AI Literacy`)
data$LogAILT <- log(data$`AI Literacy`)
summary(data$LogAILT)


# Calculate Cronbach's alpha for the four receptivity measures
cronbach_alpha_result <- alpha(data[, c(10,11,12,13)])

# Print the result
cronbach_alpha_result$total$raw_alpha #.983


summary(data$`AI Receptivity`)

# regression with HDI and its components as controls
data$LogIncome <- log(data$`Income`)


# regression of AI Receptivity on AI Literacy
# Run the linear mode
model1 <- lm(`AI Receptivity` ~ LogAILT, data=data)

# Get the summary of the model
summary(model1)
confint(model1)


# Filter out observations from the US
data_filtered <- data[data$Country != "US", ]

# Run the linear model on the filtered dataset
model1_filtered <- lm(`AI Receptivity` ~ LogAILT, data=data_filtered)

# Get the summary of the model
summary(model1_filtered)
confint(model1_filtered)

# regression with separate measures of AI receptivity
modelA <- lm(`Will change my life` ~ LogAILT, data=data)
summary(modelA)
modelB <- lm(`Make life easier` ~ LogAILT, data=data)
summary(modelB)
modelC <- lm(`Benefits` ~ LogAILT, data=data)
summary(modelC)
modelD <- lm(`trust companies with AI` ~ LogAILT, data=data)
summary(modelD)





# Run the linear model 
model2 <- lm(`AI Receptivity` ~ LogAILT + `Human Development Index`, data=data)

# Get the summary of the model
summary(model2)
confint(model2)


# Run the linear model
model3 <- lm(`AI Receptivity` ~ LogAILT + `Life Expectancy` + `Education` + LogIncome, data=data)

# Get the summary of the model
summary(model3)
confint(model3)


# Run the linear model
model4 <- lm(`AI Receptivity` ~ LogAILT + `Life Expectancy` + `Education` + LogIncome+GDP_growth_rate+Population_Growth, data=data)


# Get the summary of the model
summary(model4)
confint(model4)

library(stargazer)
stargazer(model1, model2, model3,model4, type = "text")
