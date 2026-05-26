library(readxl)
options(scipen=999)

file_path <- "Enter your file path here"

# Reading the Excel file
data <- read_excel(file_path)
data<-data[data$`filter_$`==1,]

# Viewing the first few rows of the dataset
head(data)

#statistics
mean(data$Age)
sd(data$Age)

gender_counts <- table(data$Gender)
gender_proportions <- prop.table(gender_counts)
(gender_percentages <- gender_proportions * 100)

summary(data$SC0)
sd(data$SC0)



model1 <- lm(Ethical26Items ~ SC0, data=data)

# Get the summary of the model
summary(model1)
confint(model1)

# model with controls
data$Gender_fac<-as.factor(data$Gender)
model1_controls <- lm(Ethical26Items ~ SC0+Gender_fac+Age, data=data)

# Get the summary of the model
summary(model1_controls)
confint(model1_controls)


#sq root transform

# Run the linear model
data$SC0sqrt<-sqrt(data$SC0)

model1sq <- lm(Ethical26Items ~ SC0sqrt, data=data)

# Get the summary of the model
summary(model1sq)
confint(model1sq)
