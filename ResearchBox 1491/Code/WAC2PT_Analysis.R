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


model1 <- lm(AvgCapability ~ SC0, data=data)

# Get the summary of the model
summary(model1)
confint(model1)

#model 1 with controls
data$Gender_fac<-as.factor(data$Gender)

model1 <- lm(AvgCapability ~ SC0+Gender_fac+Age, data=data)

# Get the summary of the model
summary(model1)
confint(model1)

